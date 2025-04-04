import os

import httpx
from auth0_ai_llamaindex.ciba import get_access_token
from llama_index.core.tools import FunctionTool


def trade_tool_function(ticker: str, qty: int) -> str:
    access_token = get_access_token()

    if not access_token:
        raise ValueError("Access token not found")

    headers = {
        "Authorization": f"{access_token["type"]} {access_token["value"]}",
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


trade_tool = FunctionTool.from_defaults(
    name="trade_tool",
    description="Use this function to trade a stock",
    fn=trade_tool_function,
)
