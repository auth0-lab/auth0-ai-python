from typing import Annotated
from llama_index.core.tools import FunctionTool

def check_country_holiday_function(
    date,
    country: Annotated[str, "The country code in ISO 3166-1 alpha-2 format. For example, \"US\" for the United States."]
) -> str:
    return f"[MOCKED RESULT] {date} is recognized as a holiday in {country}"

check_country_holiday_tool = FunctionTool.from_defaults(
    name="check_country_holiday",
    description="Use this function to check if a given date is a holiday in the given country",
    fn=check_country_holiday_function,
)
