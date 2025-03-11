from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel
from langchain_core.tools import StructuredTool
from langchain_core.runnables import ensure_config
from auth0_ai.authorizers.types import AuthParams
from auth0_ai.authorizers.fga_authorizer import FGAAuthorizer, FGAAuthorizerOptions

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

async def buy_tool_function(auth: AuthParams, params: BuySchema) -> dict[str, Any]:
    allowed = auth.get("allowed", False)
    ticker = params.get("ticker")
    qty = params.get("qty")

    if allowed:
        # send email confirmation (mocked)
        return {"ticker": ticker, "qty": qty}

    # send email confirmation (mocked)
    return {"error": f"The user is not allowed to buy {ticker}."}

func=use_fga(buy_tool_function)

buy_tool = StructuredTool(
    name="buy",
    description="Use this function to buy stocks",
    args_schema=BuySchema,
    func=func,
    coroutine=func,
)
