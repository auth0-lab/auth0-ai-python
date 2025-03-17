from datetime import datetime, timezone
from llama_index.core.tools import FunctionTool
from langchain_auth0_ai.fga.fga_authorizer import FGAAuthorizer, FGAAuthorizerOptions
from ..context import Context

def buy_tool (context: Context):
    fga = FGAAuthorizer.create()

    def build_fga_query(tool_input):
        return {
            "user": f"user:{context.get("user_id")}",
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

    return FunctionTool.from_defaults(
        fn=func,
        async_fn=func,
        name="buy",
        description="Use this function to buy stocks",
    )
