from datetime import datetime, timedelta

import requests
from auth0_ai_langchain.federated_connections import (
    FederatedConnectionError,
    get_access_token_for_connection,
)
from langchain_core.tools import StructuredTool
from pydantic import BaseModel


class CheckUserCalendarSchema(BaseModel):
    date: datetime


def add_hours(dt: datetime, hours: int) -> str:
    return (dt + timedelta(hours=hours)).isoformat()


def check_user_calendar_tool_function(date: datetime):
    credentials = get_access_token_for_connection()
    if not credentials:
        raise ValueError(
            "Authorization required to access the Federated Connection API")

    url = "https://www.googleapis.com/calendar/v3/freeBusy"
    body = {
        "timeMin": date.isoformat() + "Z",
        "timeMax": add_hours(date, 1) + "Z",
        "timeZone": "UTC",
        "items": [{"id": "primary"}]
    }

    response = requests.post(
        url,
        headers={"Authorization": f"{credentials["token_type"]} {credentials["access_token"]}"},
        json=body
    )

    if response.status_code != 200:
        if response.status_code == 401:
            raise FederatedConnectionError(
                "Authorization required to access the Federated Connection API")
        raise ValueError(
            f"Invalid response from Google Calendar API: {response.status_code} - {response.text}")

    busy_resp = response.json()
    return {"available": len(busy_resp["calendars"]["primary"]["busy"]) == 0}


check_user_calendar_tool = StructuredTool(
    name="check_user_calendar",
    description="Use this function to check if the user is available on a certain date and time",
    args_schema=CheckUserCalendarSchema,
    func=check_user_calendar_tool_function,
)
