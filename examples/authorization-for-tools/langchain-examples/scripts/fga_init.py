import os
import asyncio
from openfga_sdk import OpenFgaClient, ConsistencyPreference, TypeName, ClientConfiguration, ReadRequestTupleKey
from openfga_sdk.client.models import ClientWriteRequest, ClientTuple
from openfga_sdk.credentials import Credentials, CredentialConfiguration
from dotenv import load_dotenv
from datetime import datetime, timezone
from dateutil.relativedelta import relativedelta

load_dotenv()

def main():
    asyncio.run(async_main())

def start_of_month(date: datetime) -> datetime:
    return datetime(date.year, date.month, 1, 0, 0, 0, 0, tzinfo=timezone.utc)

def end_of_month(date: datetime) -> datetime:
    last_day = date.replace(day=1) + relativedelta(months=1) - relativedelta(days=1)
    return datetime(last_day.year, last_day.month, last_day.day, 23, 59, 59, 999999, tzinfo=timezone.utc)

async def async_filter(arr, predicate):
    results = await asyncio.gather(*(predicate(value) for value in arr))
    return [value for value, result in zip(arr, results) if not result]

async def async_main():
    configuration = ClientConfiguration(
            api_url=os.getenv("FGA_API_URL", "https://api.us1.fga.dev"),
            store_id=os.getenv("FGA_STORE_ID"),
            credentials=Credentials(
                method="client_credentials",
                configuration=CredentialConfiguration(
                    api_issuer=os.getenv("FGA_API_TOKEN_ISSUER", "auth.fga.dev"),
                    api_audience=os.getenv("FGA_API_AUDIENCE", "https://api.us1.fga.dev/"),
                    client_id=os.getenv("FGA_CLIENT_ID"),
                    client_secret=os.getenv("FGA_CLIENT_SECRET"),
                )
            )
        )
    
    async with OpenFgaClient(configuration) as fga_client:

        # 01. WRITE MODEL
        model = await fga_client.write_authorization_model({
            "schema_version": "1.1",
            "type_definitions": [
                {"type": "user", "relations": {}},
                {
                    "type": "asset",
                    "relations": {
                        "_restricted_employee": {"this": {}},
                        "can_buy": {
                            "difference": {
                                "base": {"this": {}},
                                "subtract": {"computedUserset": {"relation": "restricted"}},
                            },
                        },
                        "restricted": {"computedUserset": {"relation": "_restricted_employee"}},
                    },
                    "metadata": {
                        "relations": {
                            "_restricted_employee": {
                                "directly_related_user_types": [
                                    {
                                        "type": "company",
                                        "condition": "is_trading_window_closed",
                                        "relation": "employee",
                                    }
                                ],
                            },
                            "can_buy": {
                                "directly_related_user_types": [
                                    {"type": "user"},
                                    {"type": "user", "wildcard": {}},
                                ],
                            },
                            "restricted": {"directly_related_user_types": []},
                        },
                    },
                },
                {
                    "type": "company",
                    "relations": {"employee": {"this": {}}},
                    "metadata": {
                        "relations": {
                            "employee": {"directly_related_user_types": [{"type": "user"}]},
                        },
                    },
                },
            ],
            "conditions": {
                "is_trading_window_closed": {
                    "name": "is_trading_window_closed",
                    "expression": "current_time >= from && current_time <= to",
                    "parameters": {
                        "current_time": {"type_name": TypeName.TIMESTAMP},
                        "from": {"type_name": TypeName.TIMESTAMP},
                        "to": {"type_name": TypeName.TIMESTAMP},
                    },
                },
            },
        })

        print("NEW MODEL ID:", model.authorization_model_id)
        
        # Company Stock Restriction
        assets_tuples = [
            {"user": "user:*", "relation": "can_buy", "object": "asset:ZEKO"},
            {"user": "user:*", "relation": "can_buy", "object": "asset:ATKO"},
        ]

        # ATKO Employee
        restricted_employees_tuples = [
            {"user": "user:john", "relation": "employee", "object": "company:ATKO"},
        ]

        # ATKO Trading Window Restriction
        now = datetime.now()
        print(start_of_month(now).isoformat(), end_of_month(now).isoformat())
        restricted_assets_tuples = [
            {
                "user": "company:ATKO#employee",
                "relation": "_restricted_employee",
                "object": "asset:ATKO",
                "condition": {
                    "name": "is_trading_window_closed",
                    "context": {
                        "from": start_of_month(now).isoformat(),
                        "to": end_of_month(now).isoformat(),
                    },
                },
            },
        ]

        # 02. CONFIGURE PRE-DEFINED TUPLES
        async def tuple_exists(t) -> bool:
            request = ReadRequestTupleKey(user=t["user"], relation=t["relation"], object=t["object"])
            response = await fga_client.read(request, {"consistency": ConsistencyPreference.HIGHER_CONSISTENCY})
            return len(response.tuples) > 0

        tuples_to_write = await async_filter(
            assets_tuples + restricted_assets_tuples + restricted_employees_tuples,
            tuple_exists,
        )

        if tuples_to_write:
            await fga_client.write(
                ClientWriteRequest(writes=[ClientTuple(**t) for t in tuples_to_write]),
                {
                    "authorization_model_id": model.authorization_model_id,
                }
            )

        await fga_client.close()
        print("Done!")

if __name__ == "__main__":
    main()
