from typing import Any, AsyncIterable, Literal
import os
from pydantic import BaseModel
import httpx

from auth0.authentication.get_token import GetToken
from auth0.management import Auth0

from auth0_ai_langchain.auth0_ai import Auth0AI
from auth0_ai_langchain.ciba import get_ciba_credentials

from langchain_core.runnables.config import RunnableConfig
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.prebuilt import create_react_agent
from langgraph_sdk import get_client
from langchain_google_genai import ChatGoogleGenerativeAI


auth0_ai = Auth0AI(auth0={
    "domain": os.getenv("HR_AUTH0_DOMAIN"), "client_id": os.getenv("HR_AGENT_AUTH0_CLIENT_ID"), "client_secret": os.getenv("HR_AGENT_AUTH0_CLIENT_SECRET")
})

with_async_user_confirmation = auth0_ai.with_async_user_confirmation(
    scope='stock:trade',
    audience=os.getenv('HR_API_AUTH0_AUDIENCE'),
    binding_message='Please authorize the sharing of your employee details.',
    user_id=lambda employee_id, **__: employee_id,
    # on_authorization_request='block',
)

get_token = GetToken(domain=os.getenv("HR_AUTH0_DOMAIN"), client_id=os.getenv("HR_AGENT_AUTH0_CLIENT_ID"), client_secret=os.getenv("HR_AGENT_AUTH0_CLIENT_SECRET"))

def get_langgraph_client():
    return get_client(url=os.getenv("HR_AGENT_LANGGRAPH_BASE_URL"))

@tool
def get_employee_id_by_email(work_email: str) -> dict[str, Any] | None:
    """Return the employee ID by email.

    Args:
        work_email (str): The employee's work email.

    Returns:
        dict: A dictionary containing the employee ID if it exists, otherwise None.
    """
    try:
        user = Auth0(
            domain=get_token.domain,
            token=get_token.client_credentials(f"https://{os.getenv('HR_AUTH0_DOMAIN')}/api/v2/")["access_token"]
        ).users_by_email.search_users_by_email(email=work_email, fields=["user_id"])[0]

        return {"employee_id": user["user_id"]} if user else None
    except Exception as e:
        return {'error': 'Unexpected response from API.'}

@tool
async def is_active_employee(first_name: str, last_name: str, employee_id: str) -> dict[str, Any]:
    """Confirm whether a person is an active employee of the company.

    Args:
        first_name (str): The employee's first name.
        last_name (str): The employee's last name.
        employee_id (str): The employee's identification.

    Returns:
        dict: A dictionary containing the employment status, or an error message if the request fails.
    """
    try:
        credentials = get_ciba_credentials()
        response = await httpx.AsyncClient().get(f"{os.getenv('HR_API_BASE_URL')}/employees/{employee_id}", headers={
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
    except httpx.HTTPError as e:
        return {'error': f'API request failed: {e}'}
    except Exception as e:
        return {'error': 'Unexpected response from API.'}

class ResponseFormat(BaseModel):
    """Respond to the user in this format."""

    status: Literal['input_required', 'completed', 'error'] = 'input_required'
    message: str

class HRAgent:
    SUPPORTED_CONTENT_TYPES = ['text', 'text/plain']

    AGENT_NAME: str = 'hr_agent'

    SYSTEM_INSTRUCTION: str = """
    You are an agent who handles external verification requests about Staff0 employees made by third parties.

    Do not attempt to answer unrelated questions or use tools for other purposes.

    If you are asked about a person's employee status using their employee ID, use the `is_active_employee` tool.
    If they provide a work email instead, first call the `get_employee_id_by_email` tool to get the employee ID, and then use `is_active_employee`.
    """

    RESPONSE_FORMAT_INSTRUCTION: str = """
    Select status as completed if the request is complete
    Select status as input_required if the input is a pending action from user
    Set response status to error if the input indicates an error
    """

    async def _get_agent_response(self, config: RunnableConfig):
        client = get_langgraph_client()
        current_state = await client.threads.get_state(config["configurable"]["thread_id"])

        interrupts = current_state['tasks'][0].get('interrupts', []) if current_state['tasks'] else []
        if len(interrupts) > 0:
            # TODO: is_task_complete and require_user_input should be set based on interrupt type
            return {
                'is_task_complete': False,
                'require_user_input': True,
                'content': interrupts[0]["value"]["message"],
            }

        structured_response = current_state["values"].get("structured_response")
        if structured_response and 'status' in structured_response and 'message' in structured_response:
            if structured_response['status'] in {'input_required', 'error'}:
                return {
                    'is_task_complete': False,
                    'require_user_input': True,
                    'content': structured_response['message'],
                }
            if structured_response['status'] == 'completed':
                return {
                    'is_task_complete': True,
                    'require_user_input': False,
                    'content': structured_response['message'],
                }

        return {
            'is_task_complete': False,
            'require_user_input': True,
            'content': 'We are unable to process your request at the moment. Please try again.',
        }

    async def invoke(self, query: str, session_id: str) -> dict[str, Any]:
        client = get_langgraph_client()
        input: dict[str, Any] = {'messages': [('user', query)]}
        config: RunnableConfig = {'configurable': {'thread_id': session_id}}

        await client.runs.create(session_id, assistant_id=self.AGENT_NAME, input=input, if_not_exists='create')
        return await self._get_agent_response(config)

    async def stream(self, query: str, session_id: str) -> AsyncIterable[dict[str, Any]]:
        client = get_langgraph_client()
        input: dict[str, Any] = {'messages': [('user', query)]}
        config: RunnableConfig = {'configurable': {'thread_id': session_id}}
        
        async for item in client.runs.stream(session_id, self.AGENT_NAME, input=input, stream_mode=['values'], if_not_exists='create'):
            message = item.data['messages'][-1] if 'messages' in item.data else None
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

        yield await self._get_agent_response(config)

graph = create_react_agent(
    ChatGoogleGenerativeAI(model='gemini-2.0-flash'),
    tools=ToolNode(
        [
            get_employee_id_by_email,
            with_async_user_confirmation(is_active_employee),
        ],
        handle_tool_errors=False
    ),
    name=HRAgent.AGENT_NAME,
    prompt=HRAgent.SYSTEM_INSTRUCTION,
    response_format=(HRAgent.RESPONSE_FORMAT_INSTRUCTION, ResponseFormat),
    debug=True,
)
