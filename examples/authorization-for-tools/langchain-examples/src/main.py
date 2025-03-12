import os
import asyncio
import questionary
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph_sdk import get_client

USER_ID = "john"

def main():
    asyncio.run(async_main())

async def async_main():
    try:
        messages: list[BaseMessage] = []
        client = get_client(url=os.getenv("LANGGRAPH_API_URL", "http://localhost:54367"))
        thread = await client.threads.create()

        print("<Enter a command (type 'exit' to quit)>\n\n")
        
        while True:
            message = await questionary.text(f"User (ID={USER_ID}) ·").ask_async()
            
            if message.lower() == "exit":
                print("Goodbye!")
                break
            
            messages.append(HumanMessage(message))

            wait_result = await client.runs.wait(
                thread["thread_id"],
                "agent",
                input={"messages": messages},
                config={"configurable":{"user_id": USER_ID}}
            )
            
            if wait_result and "messages" in wait_result:
                last_message = wait_result["messages"][-1]["content"]
                print(f"Assistant · {last_message}\n")
    
    except Exception as err:
        print(f"Agent error: {err}")

if __name__ == "__main__":
    main()
