from datetime import datetime
from llama_index.llms.openai import OpenAI
from llama_index.core.agent.workflow import FunctionAgent

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

llm = OpenAI(model="gpt-4o-mini")

agent = FunctionAgent(
    llm=llm,
    system_prompt=system_prompt,
    tools=[trade_tool],
    verbose=True
)
