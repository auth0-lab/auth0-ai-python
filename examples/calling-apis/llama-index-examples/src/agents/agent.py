from datetime import datetime
from llama_index.agent.openai import OpenAIAgent

from .memory import get_memory
from .tools.check_user_calendar import check_user_calendar_tool
from .tools.list_channels import list_slack_channels_tool
from .tools.list_repositories import list_github_repositories_tool


system_prompt = f"""You are an assistant designed to answer random user's questions.
**Additional Guidelines**:
- Today’s date for reference: {datetime.now().isoformat()}
"""


async def get_agent(user_id: str, chat_id: str):
    chat_memory = await get_memory(user_id, chat_id)
    return OpenAIAgent.from_tools(
        model="gpt-4o",
        memory=chat_memory,
        system_prompt=system_prompt,
        tools=[check_user_calendar_tool, list_github_repositories_tool,
               list_slack_channels_tool],
        verbose=True
    )
