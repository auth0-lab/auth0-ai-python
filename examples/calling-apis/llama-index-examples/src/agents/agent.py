from datetime import datetime
from llama_index.llms.openai import OpenAI
from llama_index.core.agent.workflow import FunctionAgent

from .tools.check_user_calendar import check_user_calendar_tool
from .tools.list_channels import list_slack_channels_tool
from .tools.list_repositories import list_github_repositories_tool


system_prompt = f"""You are an assistant designed to answer random user's questions.
**Additional Guidelines**:
- Today’s date for reference: {datetime.now().isoformat()}
"""

llm = OpenAI(model="gpt-4o-mini")

agent = FunctionAgent(
    llm=llm,
    system_prompt=system_prompt,
    tools=[check_user_calendar_tool, list_github_repositories_tool,
           list_slack_channels_tool],
    verbose=True
)
