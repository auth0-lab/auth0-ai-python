from __future__ import annotations
from typing import Any, Dict
import time
from auth0.authentication import GetToken
from auth0.authentication.async_token_verifier import AsyncAsymmetricSignatureVerifier


class TokenManager:
    """
    Manages token operations, including exchange, refresh, and validation.
    """
    def __init__(self, auth_client: Any):
        """
        Initialize token manager.
        Args:
            auth_client: Parent AIAuth instance
        """
        self.auth_client = auth_client
        self.token_verifier = AsyncAsymmetricSignatureVerifier(
            jwks_url=f"https://{auth_client.domain}/.well-known/jwks.json"
        )

    def exchange_code_for_tokens(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens.
        Args:
            code: Authorization code from Auth0
        Returns:
            Dict containing access token, refresh token, and ID token
        """
        get_token = GetToken(
            self.auth_client.domain,
            self.auth_client.client_id,
            self.auth_client.client_secret
        )
        return get_token.authorization_code(
            code=code,
            redirect_uri=self.auth_client.redirect_uri,
            grant_type="authorization_code"
        )
    
    def get_token_set(self, token_data: dict, existing_refresh_token: str | None = None) -> dict:
        """
        Format token data with expiry time.
        Args:
            token_data: Raw token data from Auth0
            existing_refresh_token: Optional existing refresh token to preserve
        Returns:
            Formatted token data with expiry information
        """
        return {
            "access_token": token_data.get("access_token"),
            "expires_at": {"epoch": int(time.time()) + token_data["expires_in"]},
            "refresh_token": token_data.get("refresh_token", existing_refresh_token),
            "id_token": token_data.get("id_token"),
            "scope": token_data.get("scope"),
        }
    
    async def verify_id_token(self, id_token: str) -> Dict[str, Any]:
        """
        Verify and decode ID token.
        Args:
            id_token: ID token to verify
        Returns:
            Decoded token claims
        """
        return await self.token_verifier.verify_signature(id_token)
    
    def refresh_tokens(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.
        Args:
            refresh_token: Refresh token to use
        Returns:
            New token set
        """
        token_client = GetToken(
            self.auth_client.domain,
            self.auth_client.client_id,
            self.auth_client.client_secret
        )
        return token_client.refresh_token(refresh_token=refresh_token)
    

    def get_3rd_party_token(self, connection: str) -> dict[str, Any]:
        return self.get_upstream_token(connection, self.get_refresh_token())

    def tokeninfo(self) -> dict[str, Any]:
        id_token = self.get_id_token()
        self.parent.post()
        data: dict[str, Any] = self.parent.get(
            url=f"https://{self.parent.domain}/tokeninfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return data

    def get_upstream_token(
        self,
        connection: str,
        refresh_token: str,
        additional_scopes: str | None = None
    ) -> Dict[str, Any]:
        """
        Get token for federated connection.
        Args:
            connection: Name of the connection (e.g., 'github')
            refresh_token: Refresh token to use
            additional_scopes: Optional additional scopes to request
        Returns:
            Token for the federated connection
        """
        token_client = GetToken(
            self.auth_client.domain,
            self.auth_client.client_id,
            self.auth_client.client_secret
        )
        return token_client.federated_connection_access_token(
            subject_token_type="urn:ietf:params:oauth:token-type:refresh_token",
            subject_token=refresh_token,
            requested_token_type="http://auth0.com/oauth/token-type/federated-connection-access-token",
            connection=connection,
            grant_type="urn:auth0:params:oauth:grant-type:token-exchange:federated-connection-access-token"
        )
    
    def get_userinfo(self, access_token: str) -> Dict[str, Any]:
        """
        Get user information using access token.
        Args:
            access_token: Access token to use
        Returns:
            User profile information
        """
        return self.auth_client.get(
            url=f"https://{self.auth_client.domain}/userinfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
    
    async def get_tokeninfo(self, id_token: str, access_token: str) -> Dict[str, Any]:
        """
        Get detailed token information.
        Args:
            id_token: ID token
            access_token: Access token
        Returns:
            Detailed token information
        """
        return await self.auth_client.get(
            url=f"https://{self.auth_client.domain}/tokeninfo",
            headers={"Authorization": f"Bearer {access_token}"}
        )
    
    def validate_tokens(self, token_data: Dict[str, Any]) -> bool:
        """
        Check if tokens are still valid.
        Args:
            token_data: Token data to validate
        Returns:
            True if tokens are valid, False otherwise
        """
        if not token_data.get("expires_at"):
            return False
        expiry = token_data["expires_at"].get("epoch", 0)
        return time.time() < expiry
    
    # Session Token Methods (used in User.py)
    def get_id_token(self, user_id: str) -> Dict[str, Any]:
        if user_id in self.auth_client.session_manager._get_stored_sessions():
            return (self.auth_client.session_manager.get_encrypted_session(user_id).get("tokens").get("id_token"))
        else:
            return {"user_id not found in session store"}
        
    def get_refresh_token(self, user_id: str) -> Dict[str, Any]:
        if user_id in self.auth_client.session_manager._get_stored_sessions():
            return (self.auth_client.session_manager.get_encrypted_session(user_id).get("tokens").get("refresh_token"))
        else:
            return {"user_id not found in session store"}
        
    def get_access_token(self, user_id: str) -> Dict[str, Any]:
        if user_id in self.auth_client.session_manager._get_stored_sessions():
            return (self.auth_client.session_manager.get_encrypted_session(user_id).get("tokens").get("access_token"))
        else:
            return {"user_id not found in session store"}

