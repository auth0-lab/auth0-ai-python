import os
import asyncio
from openfga_sdk import OpenFgaClient, ConsistencyPreference, ClientConfiguration, ReadRequestTupleKey
from openfga_sdk.client.models import ClientWriteRequest, ClientTuple
from openfga_sdk.credentials import Credentials, CredentialConfiguration
from dotenv import load_dotenv

load_dotenv()

def main():
    asyncio.run(async_main())

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
                {
                "type": "user",
                "relations": {}
                },
                {
                "type": "doc",
                "relations": {
                    "owner": {
                    "this": {}
                    },
                    "viewer": {
                    "this": {}
                    },
                    "can_view": {
                    "union": {
                        "child": [
                        {
                            "computedUserset": {
                            "relation": "viewer"
                            }
                        },
                        {
                            "computedUserset": {
                            "relation": "owner"
                            }
                        }
                        ]
                    }
                    },
                    "can_edit": {
                    "computedUserset": {
                        "relation": "owner"
                    }
                    }
                },
                "metadata": {
                    "relations": {
                    "owner": {
                        "directly_related_user_types": [
                        {
                            "type": "user"
                        }
                        ]
                    },
                    "viewer": {
                        "directly_related_user_types": [
                        {
                            "type": "user"
                        },
                        {
                            "type": "user",
                            "wildcard": {}
                        }
                        ]
                    }
                    }
                }
                }
            ]
            })

        print("NEW MODEL ID:", model.authorization_model_id)

        # 02. CONFIGURE PRE-DEFINED TUPLES
        tuples = [
            {"user": "user:*", "relation": "viewer", "object": "doc:public-doc"},
            {"user": "user:user1", "relation": "viewer", "object": "doc:private-doc"},
        ]
        
        async def tuple_exists(t) -> bool:
            request = ReadRequestTupleKey(user=t["user"], relation=t["relation"], object=t["object"])
            response = await fga_client.read(request, {"consistency": ConsistencyPreference.HIGHER_CONSISTENCY})
            return len(response.tuples) > 0

        tuples_to_write = await async_filter(tuples, tuple_exists)

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
