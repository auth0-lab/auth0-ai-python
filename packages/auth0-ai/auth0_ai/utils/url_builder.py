from __future__ import annotations
from typing import Any, Dict
import json
from urllib.parse import urlencode
from auth0.authentication.pushed_authorization_requests import PushedAuthorizationRequests

class URLBuilder:
    """
    Handles construction of Auth0 authorization URLs and PAR requests.
    Maintains original URL building logic from auth_client.py
    """
    def __init__(self, auth_client: Any):
        """
        Initialize URL builder.
        Args:
            auth_client: Parent AIAuth instance
        """
        self.auth_client = auth_client
        
    def get_authorize_url(
        self,
        state: str,
        connection: str | None = None,
        scope: str | None = None,
        additional_scopes: str | None = None,
        **kwargs
    ) -> str:
        """
        Generate authorization URL.
        Args:
            state: State parameter for CSRF protection
            connection: Auth0 connection to use
            scope: OAuth scope
            additional_scopes: Additional connection-specific scopes
            **kwargs: Additional parameters to include in the URL
        Returns:
            Complete authorization URL
        """
        # Base URL parameters
        params = {
            "response_type": "code",
            "client_id": self.auth_client.client_id,
            "redirect_uri": self.auth_client.redirect_uri,
            "grant_type": "authorization_code",
            "state": state
        }
        # Add optional parameters
        if connection is not None:
            params["connection"] = connection
        if scope is not None:
            params["scope"] = scope
        if additional_scopes is not None:
            params["connection_scope"] = additional_scopes
        # Add any additional custom arguments
        params.update(kwargs)
        # Construct URL
        query_string = urlencode(params)
        return f"https://{self.auth_client.domain}/authorize?{query_string}"
    
    def get_authorize_par_url(self, state: str, request_uri: str) -> str:
        """
        Generate PAR authorization URL.
        Args:
            state: State parameter for CSRF protection
            request_uri: PAR request URI
        Returns:
            Complete PAR authorization URL
        """
        params = {
            "client_id": self.auth_client.client_id,
            "state": state,
            "request_uri": request_uri
        }
        query_string = urlencode(params)
        return f"https://{self.auth_client.domain}/authorize?{query_string}"
    async def create_par_request(
        self,
        state: str,
        connection: str,
        id_token: str,
        scope: str | None = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Create a pushed authorization request.
        Args:
            state: State parameter for CSRF protection
            connection: Connection to link
            id_token: ID token for the primary user
            scope: OAuth scope
            **kwargs: Additional parameters
        Returns:
            PAR response containing request_uri
        """
        par_client = PushedAuthorizationRequests(
            self.auth_client.domain,
            self.auth_client.client_id,
            self.auth_client.client_secret
        )
        # Prepare authorization details for account linking
        auth_details = [{
            "type": "link_account",
            "requested_connection": connection
        }]
        # Build PAR request
        par_request = {
            "response_type": "code",
            "nonce": kwargs.get("nonce", "mynonce"),
            "redirect_uri": self.auth_client.redirect_uri,
            "audience": kwargs.get("audience", "my-account"),
            "state": state,
            "authorization_details": json.dumps(auth_details),
            "scope": scope or "openid profile",
            "id_token_hint": id_token,
            **kwargs
        }
        return await par_client.pushed_authorization_request(**par_request)