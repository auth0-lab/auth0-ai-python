import asyncio
import os
from auth0_ai_langchain.async_authorization import GraphResumer
from langgraph_sdk import get_client

async def main():
    resumer = GraphResumer(
        lang_graph=get_client(url=os.getenv("LANGGRAPH_API_URL", "http://localhost:54367")),
        filters={"graph_id": "conditional-trade"},
    )

    resumer \
        .on_resume(lambda thread: print(f"Attempting to resume thread {thread['thread_id']} from interruption {thread['interruption_id']}")) \
        .on_error(lambda err: print(f"Error in GraphResumer: {str(err)}"))

    resumer.start()
    print("Started Async Auth Graph Resumer.")
    print("The purpose of this service is to monitor interrupted threads by Auth0AI Async Authorizer and resume them.")

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("Stopping Async Auth Graph Resumer...")
        resumer.stop()

asyncio.run(main())
