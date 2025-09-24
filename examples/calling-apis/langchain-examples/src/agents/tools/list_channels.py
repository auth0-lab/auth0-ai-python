from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from pydantic import BaseModel
from langchain_core.tools import StructuredTool
from auth0_ai_langchain.token_vault import get_credentials_from_token_vault, TokenVaultError
from src.auth0.auth0_ai import with_slack_access


class EmptySchema(BaseModel):
    pass


def list_channels_tool_function():
    # Get the access token from Auth0 AI
    credentials = get_credentials_from_token_vault()

    # Slack SDK
    try:
        client = WebClient(token=credentials["access_token"])
        response = client.conversations_list(
            exclude_archived=True,
            types="public_channel,private_channel",
            limit=10
        )
        channels = response['channels']
        channel_names = [channel['name'] for channel in channels]
        return channel_names
    except SlackApiError as e:
        if e.response['error'] == 'not_authed':
            raise TokenVaultError(
                "Authorization required to access the Federated Connection API")

        raise ValueError(f"An error occurred: {e.response['error']}")


list_slack_channels_tool = with_slack_access(StructuredTool(
    name="list_slack_channels",
    description="List channels for the current user on Slack",
    args_schema=EmptySchema,
    func=list_channels_tool_function,
))
