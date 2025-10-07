from llama_index.core.storage.chat_store import SimpleChatStore
from llama_index.core.memory import ChatMemoryBuffer

chat_store = SimpleChatStore()


async def get_memory(user_id: str, chat_id: str):
    return ChatMemoryBuffer.from_defaults(
        token_limit=3000,
        chat_store=chat_store,
        chat_store_key=f"{user_id}_{chat_id}",
    )
