import os
from dotenv import load_dotenv
import httpx
from llama_index.core.tools import FunctionTool

from auth0_ai_llamaindex.async_auth import get_async_authorization_credentials
from ...auth0.auth0_ai import with_async_user_confirmation
load_dotenv()


def trade_tool_function(ticker: str, qty: int) -> str:
    credentials = get_async_authorization_credentials()

    if not credentials:
        raise ValueError("Access token not found")

    headers = {
        "Authorization": f"{credentials["token_type"]} {credentials["access_token"]}",
        "Content-Type": "application/json"
    }

    trade_data = {"ticker": ticker, "qty": qty}

    try:
        response = httpx.post(os.getenv("API_URL"),
                              json=trade_data, headers=headers)
        if response.status_code == 200:
            return "Trade successful"
        else:
            return f"Trade failed: {response.status_code} - {response.text}"
    except httpx.HTTPError as e:
        return f"HTTP request failed: {str(e)}"


trade_tool = with_async_user_confirmation(FunctionTool.from_defaults(
    name="trade_tool",
    description="Use this function to trade a stock",
    fn=trade_tool_function,
))
