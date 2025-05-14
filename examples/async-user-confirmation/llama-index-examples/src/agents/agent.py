from datetime import datetime
from llama_index.agent.openai import OpenAIAgent

from .memory import get_memory
from .tools.trade import trade_tool


system_prompt = f"""You are a specialized stock trading assistant designed to
guide users through the process of buying stocks step by step.

**Important Constraints**:
- You cannot discuss, buy, or sell any stocks outside this limited list, whether real or fictional.
- You and the user can discuss the prices of these stocks, adjust stock amounts, and place buy orders through the UI.

**Additional Guidelines**:
- Today’s date for reference: {datetime.now().isoformat()}
- You may perform calculations as needed and engage in general discussion with the user.
"""


async def get_agent(user_id: str, chat_id: str):
    chat_memory = await get_memory(user_id, chat_id)
    return OpenAIAgent.from_tools(
        model="gpt-4o",
        memory=chat_memory,
        system_prompt=system_prompt,
        tools=[trade_tool],
        verbose=True
    )
