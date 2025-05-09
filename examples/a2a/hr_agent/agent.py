from typing import Any, AsyncIterable, Literal
import os
from pydantic import BaseModel
import requests
import logging

from auth0_ai_langchain.auth0_ai import Auth0AI
from auth0.authentication.get_token import GetToken
from auth0.management import Auth0

from hr_agent.prompt import agent_instruction
from auth0_ai_langchain.ciba import get_ciba_credentials

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent


logger = logging.getLogger()

auth0_ai = Auth0AI(auth0={
    "domain": os.getenv("HR_AUTH0_DOMAIN"), "client_id": os.getenv("HR_AGENT_AUTH0_CLIENT_ID"), "client_secret": os.getenv("HR_AGENT_AUTH0_CLIENT_SECRET")
})

with_async_user_confirmation = auth0_ai.with_async_user_confirmation(
    scope='stock:trade',
    audience=os.getenv('HR_API_AUTH0_AUDIENCE'),
    binding_message='Please authorize the sharing of your employee details.',
    user_id=lambda user_id, **__: user_id
)

get_token = GetToken(domain=os.getenv("HR_AUTH0_DOMAIN"), client_id=os.getenv("HR_AGENT_AUTH0_CLIENT_ID"), client_secret=os.getenv("HR_AGENT_AUTH0_CLIENT_SECRET"))

@tool
def get_employee_id_by_email(work_email: str) -> str | None:
    """Return the employee ID by email.

    Args:
        work_email (str): The employee's work email.

    Returns:
        Optional[str]: The employee ID if it exists, otherwise None.
    """
    user = Auth0(
        domain=get_token.domain,
        token=get_token.client_credentials(f"https://{os.getenv('HR_AUTH0_DOMAIN')}/api/v2/")["access_token"]
    ).users_by_email.search_users_by_email(email=work_email, fields=["user_id"])[0]
    return user["user_id"] if user else None

@tool
def is_active_employee(first_name: str, last_name: str, user_id: str) -> dict[str, Any]:
    """Confirm whether a person is an active employee of the company.

    Args:
        first_name (str): The employee's first name.
        last_name (str): The employee's last name.
        work_email (str): The employee's work email.

    Returns:
        dict: A dictionary containing the employment status, or an error message if the request fails.
    """
    try:
        credentials = get_ciba_credentials()
        response = requests.get(f"{os.getenv('HR_API_BASE_URL')}/employees/{user_id}", headers={
            "Authorization": f"{credentials['token_type']} {credentials['access_token']}",
            "Content-Type": "application/json"
        })

        if response.status_code == 404:
            return {'active': False}
        elif response.status_code == 200:
            # employee_data = response.json()
            # employee_first_name = employee_data.get("first_name", "").lower()
            # employee_last_name = employee_data.get("last_name", "").lower()

            # return (
            #     employee_first_name == first_name.lower() and
            #     employee_last_name == last_name.lower()
            # )
            return {'active': True}
        else:
            response.raise_for_status()
    except requests.HTTPError as e:
        return {'error': f'API request failed: {e}'}
    except Exception as e:
        logger.error(f'Error from is_active_employee tool: {e}')
        return {'error': 'Unexpected response from API.'}

class ResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str

class HRAgent:
    """An agent that handles HR related operations."""

    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    def __init__(self):
        self.model = ChatGoogleGenerativeAI(model='gemini-2.0-flash')
        self.tools = ToolNode(
            [
                get_employee_id_by_email,
                with_async_user_confirmation(is_active_employee),
            ],
            handle_tool_errors=False
        )

        self.graph = create_react_agent(
            self.model,
            tools=self.tools,
            checkpointer=MemorySaver(),
            prompt=agent_instruction,
            response_format=ResponseFormat,
            debug=True,
        )


    async def invoke(self, query, session_id) -> str:
        config = {'configurable': {'thread_id': session_id}}
        await self.graph.ainvoke({'messages': [('user', query)]}, config)
        return self.get_agent_response(config)

    async def stream(self, query, session_id) -> AsyncIterable[dict[str, Any]]:
        inputs = {'messages': [('user', query)]}
        config = {'configurable': {'thread_id': session_id}}

        async for item in self.graph.astream(inputs, config, stream_mode='values'):
            message = item['messages'][-1] if 'messages' in item else None
            if message:
                if (
                    isinstance(message, AIMessage)
                    and message.tool_calls
                    and len(message.tool_calls) > 0
                ):
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': 'Looking up the employment status...',
                    }
                elif isinstance(message, ToolMessage):
                    yield {
                        'is_task_complete': False,
                        'require_user_input': False,
                        'content': 'Processing the employment details..',
                    }

        yield self.get_agent_response(config)

    def get_agent_response(self, config):
        current_state = self.graph.get_state(config)
        
        interrupts = current_state.interrupts
        if len(interrupts) > 0:
            return {
                'is_task_complete': False,
                'require_user_input': True,
                'content': interrupts[0].value["message"],
            }

        structured_response = current_state.values.get('structured_response')
        if structured_response and isinstance(
            structured_response, ResponseFormat
        ):
            if (
                structured_response.status == 'input_required'
                or structured_response.status == 'error'
            ):
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response.message,
                }
            if structured_response.status == 'completed':
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': structured_response.message,
                }

        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': 'We are unable to process your request at the moment. Please try again.',
        }
