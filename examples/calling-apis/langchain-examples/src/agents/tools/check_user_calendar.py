import requests
from datetime import datetime, timedelta
from pydantic import BaseModel
from langchain_core.tools import StructuredTool
from auth0_ai.authorizers.federated_connection_authorizer import get_access_token_for_connection
from auth0_ai.interrupts.federatec_connection_interrupt import FederatedConnectionError

class CheckUserCalendarSchema(BaseModel):
    date: datetime

def add_hours(date: str, hours: int) -> str:
    dt = datetime.fromisoformat(date)
    return (dt + timedelta(hours=hours)).isoformat()

async def check_user_calendar_tool_function(date: datetime):
    access_token = get_access_token_for_connection()
    if not access_token:
        raise ValueError("Authorization required to access the Federated Connection API")
    
    url = "https://www.googleapis.com/calendar/v3/freeBusy"
    body = {
        "timeMin": date,
        "timeMax": add_hours(date, 1),
        "timeZone": "UTC",
        "items": [{"id": "primary"}]
    }
    
    response = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        },
        json=body
    )
    
    if response.status_code != 200:
        if response.status_code == 401:
            raise FederatedConnectionError("Authorization required to access the Federated Connection API")
        raise ValueError(f"Invalid response from Google Calendar API: {response.status_code} - {response.text}")
    
    busy_resp = response.json()
    return {"available": len(busy_resp["calendars"]["primary"]["busy"]) == 0}

check_user_calendar_tool = StructuredTool(
    name="check_user_calendar",
    description="Use this function to check if the user is available on a certain date and time",
    args_schema=CheckUserCalendarSchema,
    func=check_user_calendar_tool_function,
    coroutine=check_user_calendar_tool_function
)
