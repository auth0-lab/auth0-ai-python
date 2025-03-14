from datetime import datetime, timezone
from llama_index.core.tools import FunctionTool
from langchain_auth0_ai.fga.fga_authorizer import AuthParams, FGAAuthorizer, FGAAuthorizerOptions
from ..context import Context

def buy_tool (context: Context):
    fga = FGAAuthorizer.create()

    def build_fga_query(params):
        return {
            "user": f"user:{context.get("user_id")}",
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

    return FunctionTool.from_defaults(
        fn=func,
        async_fn=func,
        name="buy",
        description="Use this function to buy stocks",
    )
