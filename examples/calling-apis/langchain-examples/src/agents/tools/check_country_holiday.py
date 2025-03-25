from datetime import datetime
from pydantic import BaseModel, Field
from langchain_core.tools import StructuredTool

class CheckCountryHolidaySchema(BaseModel):
    date: datetime
    country: str = Field(..., description="The country code in ISO 3166-1 alpha-2 format. For example, \"US\" for the United States.")

def check_country_holiday_tool_function(date: datetime, country: str) -> str:
    return f"[MOCKED RESULT] {date.date()} is recognized as a holiday in {country}"

check_country_holiday_tool = StructuredTool(
    name="check_country_holiday",
    description="Use this function to check if a given date is a holiday in the given country",
    args_schema=CheckCountryHolidaySchema,
    func=check_country_holiday_tool_function,
)
