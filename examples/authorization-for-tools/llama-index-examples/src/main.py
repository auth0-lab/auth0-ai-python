import asyncio
import questionary
from datetime import datetime
from llama_index.llms.openai import OpenAI
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.core.memory import Memory


from .tools.buy import buy_tool
from dotenv import load_dotenv

load_dotenv()

USER_ID = "john"


system_prompt = f"""You are a specialized stock trading assistant designed to guide users through the process of buying stocks step by step.

**Market Scope**:
Your available market consists of only 2 stocks. Here are the details of each:

- **Ticker**: ZEKO
  **Name**: Zeko Advanced Systems Inc.
  **Summary**: Zeko Advanced Systems Inc. is a global leader in medical technology, specializing in surgical robotics, AI-driven patient monitoring, and digital health solutions.
- **Ticker**: ATKO
  **Name**: Atko Technologies Corporation
  **Summary**: Atko Technologies Corporation designs and manufactures advanced semiconductors for global industries, driving innovation in AI, gaming, and quantum computing.

**Important Constraints**:
- You cannot discuss, buy, or sell any stocks outside this limited list, whether real or fictional.
- You and the user can discuss the prices of these stocks, adjust stock amounts, and place buy orders.

**Additional Guidelines**:
- Today’s date for reference: {datetime.now().isoformat()}
- You may perform calculations as needed and engage in general discussion with the user.
"""

tools = [buy_tool({"user_id": USER_ID})]
llm = OpenAI(model="gpt-4o-mini")
memory = Memory.from_defaults(session_id="my_session", token_limit=40000)
agent = FunctionAgent(llm=llm, system_prompt=system_prompt,
                      tools=tools, verbose=False)


async def async_main():
    try:
        print("<Enter a command (type 'exit' to quit)>\n\n")

        while True:
            message = await questionary.text(f"User (ID={USER_ID}) ·").ask_async()

            if message.lower() == "exit":
                print("Goodbye!")
                break

            response = await agent.run(user_msg=message, memory=memory)
            print(f"Assistant · {response}\n")

    except Exception as err:
        print(f"Agent error: {err}")


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(async_main())


if __name__ == "__main__":
    main()
