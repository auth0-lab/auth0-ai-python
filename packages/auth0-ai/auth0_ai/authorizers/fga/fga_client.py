import os

from typing import Optional
from openfga_sdk import OpenFgaClient, ClientConfiguration
from openfga_sdk.sync import OpenFgaClient as OpenFgaClientSync

from openfga_sdk.credentials import CredentialConfiguration, Credentials


def get_openfga_client_configuration(
    fga_client_configuration: Optional[ClientConfiguration],
):
    """
    Returns a ClientConfiguration object based on the user's params, or the default values read from environment
    """
    return fga_client_configuration or ClientConfiguration(
        api_url=os.getenv("FGA_API_URL") or "https://api.us1.fga.dev",
        store_id=os.getenv("FGA_STORE_ID"),
        credentials=Credentials(
            method="client_credentials",
            configuration=CredentialConfiguration(
                api_issuer=os.getenv("FGA_API_TOKEN_ISSUER") or "auth.fga.dev",
                api_audience=os.getenv("FGA_API_AUDIENCE")
                or "https://api.us1.fga.dev/",
                client_id=os.getenv("FGA_CLIENT_ID"),
                client_secret=os.getenv("FGA_CLIENT_SECRET"),
            ),
        ),
    )


def build_openfga_client_sync(fga_client_configuration: Optional[ClientConfiguration]):
    """
    Returns an instance of the sync OpenFGA Client
    """
    return OpenFgaClientSync(get_openfga_client_configuration(fga_client_configuration))


def build_openfga_client(fga_client_configuration: Optional[ClientConfiguration]):
    """
    Returns an instance of the async OpenFGA Client
    """
    return OpenFgaClient(get_openfga_client_configuration(fga_client_configuration))
