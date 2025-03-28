import asyncio
import os
import questionary
from langchain_core.messages import BaseMessage, HumanMessage
from langgraph_sdk import get_client
from dotenv import load_dotenv
from .authenticate import authenticate

load_dotenv()

def main():
    token_response = authenticate()
    asyncio.run(async_main(token_response["refresh_token"]))

async def async_main(refresh_token: str):
    try:
        messages: list[BaseMessage] = []
        client = get_client(url=os.getenv("LANGGRAPH_API_URL", "http://localhost:54367"))
        thread = await client.threads.create()

        print("<Enter a command (type 'exit' to quit)>\n\n")
        
        while True:
            message = await questionary.text(f"User ·").ask_async()
            
            if message.lower() == "exit":
                print("Goodbye!")
                break
            
            messages.append(HumanMessage(message))

            wait_result = await client.runs.wait(
                thread["thread_id"],
                "agent",
                input={"messages": messages},
                config={"configurable":{"_credentials":{"refresh_token":refresh_token}}}
            )
            
            if wait_result and "messages" in wait_result:
                last_message = wait_result["messages"][-1]["content"]
                print(f"Assistant · {last_message}\n")
    
    except Exception as err:
        print(f"Agent error: {err}")

if __name__ == "__main__":
    main()
