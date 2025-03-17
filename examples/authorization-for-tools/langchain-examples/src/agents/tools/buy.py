from datetime import datetime, timezone
from pydantic import BaseModel
from langchain_core.tools import StructuredTool
from langchain_core.runnables import ensure_config
from langchain_auth0_ai.fga.fga_authorizer import AuthParams, FGAAuthorizer, FGAAuthorizerOptions

class BuySchema(BaseModel):
    ticker: str
    qty: int

fga = FGAAuthorizer.create()

async def build_fga_query(params):
    user_id = ensure_config().get("configurable",{}).get("user_id")
    return {
        "user": f"user:{user_id}",
        "object": f"asset:{params.get("ticker")}",
        "relation": "can_buy",
        "context": {"current_time": datetime.now(timezone.utc).isoformat()}
    }

use_fga = fga(FGAAuthorizerOptions(
    build_query=build_fga_query
))

async def buy_tool_function(auth: AuthParams, ticker: str, qty: int) -> str:
    allowed = auth.get("allowed", False)
    if allowed:
        # TODO: implement buy operation
        return f"Purchased {qty} shares of {ticker}"
    
    return f"The user is not allowed to buy {ticker}."

func=use_fga(buy_tool_function, on_error=lambda err: f"Unexpected error from buy tool: {err}")

buy_tool = StructuredTool(
    name="buy",
    description="Use this function to buy stocks",
    args_schema=BuySchema,
    func=func,
    coroutine=func,
)
