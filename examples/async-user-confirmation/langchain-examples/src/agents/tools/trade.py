import os
import httpx
from auth0_ai_langchain.async_auth import get_async_authorization_credentials
from langchain_core.tools import StructuredTool
from pydantic import BaseModel

class TradeSchema(BaseModel):
    ticker: str
    qty: int

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
        response = httpx.post(os.getenv("API_URL"), json=trade_data, headers=headers)
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Trade successful",
                "ticker": ticker,
                "qty": qty,
            }
        else:
            return {
                "success": False,
                "message": f"Trade failed: {response.status_code} - {response.text}",
            }
    except httpx.HTTPError as e:
        return {
            "success": False,
            "message": f"HTTP request failed: {str(e)}",
        }

trade_tool = StructuredTool(
    name="trade_tool",
    description="Use this function to trade a stock",
    args_schema=TradeSchema,
    func=trade_tool_function,
)
