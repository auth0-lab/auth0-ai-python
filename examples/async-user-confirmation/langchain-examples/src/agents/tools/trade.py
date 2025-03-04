import os
import httpx
from langchain_core.tools import StructuredTool
from pydantic import BaseModel
from typing import Dict, Any

class TradeSchema(BaseModel):
    ticker: str
    qty: int

def get_access_token(config: Dict[str, Any]) -> str:
    return ""  # TODO: Implement access token retrieval

def trade_tool_function(ticker: str, qty: int, config: Dict[str, Any] = {}) -> str:
    access_token = get_access_token(config)
    
    if not access_token:
        raise ValueError("Access token not found")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    trade_data = {"ticker": ticker, "qty": qty}

    try:
        response = httpx.post(os.getenv("API_URL"), json=trade_data, headers=headers)
        if response.status_code == 200:
            return "Trade successful"
        else:
            return f"Trade failed: {response.status_code} - {response.text}"
    except httpx.HTTPError as e:
        return f"HTTP request failed: {str(e)}"

trade_tool = StructuredTool(
    name="trade_tool",
    description="Use this function to trade a stock",
    args_schema=TradeSchema,
    func=trade_tool_function,
)