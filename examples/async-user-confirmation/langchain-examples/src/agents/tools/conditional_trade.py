from typing import Dict, Any
from pydantic import BaseModel
from enum import Enum
from langchain_core.tools import StructuredTool
from clients.scheduler import SchedulerClient

class MetricEnum(str, Enum):
    PE = "P/E"
    EPS = "EPS"
    PB = "P/B"
    DE = "D/E"
    ROE = "ROE"
    RSI = "RSI"
    PRICE = "price"

class OperatorEnum(str, Enum):
    equal = "="
    less_than = "<"
    less_than_or_equal = "<="
    greater_than = ">"
    greater_than_or_equal = ">="

class ConditionalTradeSchema(BaseModel):
    ticker: str
    qty: int
    metric: MetricEnum
    operator: OperatorEnum
    threshold: float

async def schedule_conditional_trade(
    ticker: str, qty: int, metric: MetricEnum, operator: OperatorEnum, threshold: float, config: Dict[str, Any] = {}
) -> str:
    await SchedulerClient().schedule({
        "graph_id": "conditional-trade",
        "config": config,
        "input": {
            "data": {
                "ticker": ticker,
                "qty": qty,
                "metric": metric,
                "operator": operator,
                "threshold": threshold
            }
        }
    })

    print("----")
    print(f"Starting conditional trading for: {ticker}")
    print("----")

    return "Conditional trading started"

conditional_trade_tool = StructuredTool(
    name="conditional_trade_tool",
    description="Use this function to trade a stock under certain conditions",
    args_schema=ConditionalTradeSchema,
    func=schedule_conditional_trade,
    coroutine=schedule_conditional_trade,
)
