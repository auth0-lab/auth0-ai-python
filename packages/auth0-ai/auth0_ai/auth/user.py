from __future__ import annotations
from typing import Any, Dict

class User:
    """
    Represents an authenticated user with token management capabilities.
    """
    def __init__(self, auth_client, user_id: str):
        """
        Initialize a User instance.
        Args:
            auth_client: The parent AIAuth instance
            user_id: The unique identifier for the user
        """
        self._auth_client = auth_client
        self._user_id = user_id
    @property
    def user_id(self) -> str:
        """Get the user's ID"""
        return self._user_id
    async def link(self, connection: str, scope: str | None = None, **kwargs) -> Dict[str, Any]:
        """
        Link another authentication provider to this user account.
        Args:
            connection: The name of the connection to link (e.g., 'github', 'google')
            scope: OAuth scope for the connection
            **kwargs: Additional parameters for the linking process
        Returns:
            Dict containing link status and user information
        """
        return await self._auth_client.link(
            primary_user_id=self.user_id,
            connection=connection,
            id_token=self.get_id_token(),
            scope=scope,
            **kwargs
        )
    async def unlink(self, connection: str, scope: str | None = None, **kwargs) -> Dict[str, Any]:
        """
        UnLink an existing authentication provider to this user account.
        Args:
            connection: The name of the connection to unlink (e.g., 'github', 'google')
            **kwargs: Additional parameters for the unlinking process
        Returns:
            Dict containing unlink status and user information
        """
        return await self._auth_client.unlink(
            primary_user_id=self.user_id,
            connection=connection,
            id_token=self.get_id_token(),
            scope=scope,
            **kwargs
        )
    def get_id_token(self) -> str:
        """Get the user's ID token"""
        return self._auth_client.token_manager.get_id_token(self.user_id)
    
    def get_access_token(self) -> str:
        """Get the user's access token"""
        return self._auth_client.token_manager.get_access_token(self.user_id)
    
    def get_refresh_token(self) -> str:
        """Get the user's refresh token"""
        return self._auth_client.token_manager.get_refresh_token(self.user_id)
    
    def get_3rd_party_token(self, connection: str) -> Dict[str, Any]:
        """
        Get access token for a linked third-party provider.
        Args:
            connection: The name of the third-party connection (e.g., 'github')
        Returns:
            Dict containing the third-party access token and related information
        """
        refresh_token = self.get_refresh_token()
        return self._auth_client.get_upstream_token(connection, refresh_token)
    
    def get_profile(self) -> Dict[str, Any]:
        """
        Get the user's profile information.
        Returns:
            Dict containing user profile data
        """
        access_token = self.get_access_token()
        return self._auth_client.token_manager.get_userinfo(access_token)
    
    async def get_token_info(self) -> Dict[str, Any]:
        """
        Get detailed information about the user's tokens.
        Returns:
            Dict containing token information
        """
        id_token = self.get_id_token()
        access_token = self.get_access_token()
        return await self._auth_client.token_manager.get_tokeninfo(id_token, access_token)
    
    def is_token_valid(self) -> bool:
        """
        Check if the user's tokens are still valid.
        Returns:
            bool indicating token validity
        """
        return self._auth_client.token_manager.validate_tokens(self.user_id)
    
    async def refresh_tokens(self) -> bool:
        """
        Refresh the user's tokens if they're expired.
        Returns:
            bool indicating if refresh was successful
        """
        refresh_token = self.get_refresh_token()
        if not refresh_token:
            return False
        return await self._auth_client.token_manager.refresh_tokens(self.user_id, refresh_token)
    
    def get_session(self) -> Dict[str, Any]:
        """
        Get the current session information for the user.
        Returns:
            Dict containing session information
        """
        return self._auth_client.get_session(self)







