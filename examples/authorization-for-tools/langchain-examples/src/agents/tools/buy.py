from datetime import datetime, timezone
from pydantic import BaseModel
from langchain_core.tools import StructuredTool
from langchain_core.runnables import ensure_config
from langchain_auth0_ai.fga.fga_authorizer import FGAAuthorizer, FGAAuthorizerOptions

class BuySchema(BaseModel):
    ticker: str
    qty: int

fga = FGAAuthorizer.create()

async def build_fga_query(tool_input):
    user_id = ensure_config().get("configurable",{}).get("user_id")
    return {
        "user": f"user:{user_id}",
        "object": f"asset:{tool_input["ticker"]}",
        "relation": "can_buy",
        "context": {"current_time": datetime.now(timezone.utc).isoformat()}
    }

def on_unauthorized(tool_input):
    return f"The user is not allowed to buy {tool_input["qty"]} shares of {tool_input["ticker"]}."

use_fga = fga(FGAAuthorizerOptions(
    build_query=build_fga_query,
    on_unauthorized=on_unauthorized,
))

async def buy_tool_function(ticker: str, qty: int) -> str:
    # TODO: implement buy operation
    return f"Purchased {qty} shares of {ticker}"

func=use_fga(buy_tool_function)

buy_tool = StructuredTool(
    name="buy",
    description="Use this function to buy stocks",
    args_schema=BuySchema,
    func=func,
    coroutine=func,
)
