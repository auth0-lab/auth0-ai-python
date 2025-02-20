from __future__ import annotations
from typing import Any
import webbrowser
import secrets
import json
from typing import Any, Dict

from auth0.authentication.async_token_verifier import AsyncAsymmetricSignatureVerifier
from auth0.authentication.pushed_authorization_requests import PushedAuthorizationRequests

from .base import BaseAuth
from .user import User
from auth0_ai.server.auth_server import AuthServer
from auth0_ai.token_module.manager import TokenManager
from auth0_ai.session_module.manager import SessionManager
from auth0_ai.state.login_state import LoginState
from auth0_ai.state.link_state import LinkState
from auth0_ai.utils.url_builder import URLBuilder

class AIAuth(BaseAuth):
    """Main authentication class that orchestrates the auth flow"""
    def __init__(
            self,
            domain: str | None = None,
            client_id: str | None = None,
            client_secret: str | None = None,
            redirect_uri: str | None = None,
            secret_key: str | None = None,
            *args, **kwargs):
        """Initialize AIAuth with all necessary components"""
        super().__init__(
            domain=domain,
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            secret_key=secret_key,
            *args, **kwargs
        )
        # Initialize token verifier
        jwk_url = f"https://{self.domain}/.well-known/jwks.json"
        self.token_verifier = AsyncAsymmetricSignatureVerifier(jwks_url=jwk_url)
        # Initialize components
        self.state_store: Dict[str, Dict[str, Any]] = {}
        self.session_manager = SessionManager(self)
        self.token_manager = TokenManager(self)
        self.url_builder = URLBuilder(self)
        # Initialize server
        self.server= AuthServer(self)

    def _generate_state(self) -> str:
        """Generate a secure random state and store it"""
        state = secrets.token_urlsafe(16)
        self.state_store[state] = {"is_completed": False}
        return state
    async def interactive_login(
        self,
        connection: str | None = None,
        scope: str | None = None,
        **kwargs
    ) -> User:
        """
        Handle interactive login flow.
        Args:
            connection: Optional connection to use
            scope: OAuth scope (default: "openid profile email")
            **kwargs: Additional parameters for authorization
        Returns:
            User instance if successful, error string if failed
        """
        if scope is None:
            scope = "openid profile email"
        # Generate state and create login state tracker
        state = self._generate_state()
        login_state = LoginState(self.state_store, state)
        # Generate authorization URL
        auth_url = self.url_builder.get_authorize_url(
            state=state,
            connection=connection,
            scope=scope,
            **kwargs
        )
        # Open browser for authentication
        try:
            webbrowser.open(auth_url)
        except webbrowser.Error:
            print(f"Please navigate here: {auth_url}")
        # Wait for authentication completion
        user_id = await login_state.wait_for_completion()
        if not user_id:
            return "login failed"
        return User(self, user_id=user_id)
    
    async def link(
        self,
        primary_user_id: str,
        connection: str,
        id_token: str,
        scope: str | None = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Handle account linking flow.
        Args:
            primary_user_id: ID of the user initiating the link
            connection: Connection to link
            id_token: ID token of the primary user
            scope: OAuth scope
            **kwargs: Additional parameters for authorization
        Returns:
            Dict containing link status and user information
        """
        state = self._generate_state()
        link_state = LinkState(self.state_store, state)
        link_state.set_user(primary_user_id)

        auth_url = self.url_builder.get_authorize_url(
            state = state,
            scope = "link_account",
            audience = "my-account",
            requested_connection = connection,
            requested_connection_scope = scope,
            id_token_hint = id_token,
            client_id = self.client_id,
            redirect_uri = self.redirect_uri,
        )

        try:
            try:
                webbrowser.open(auth_url)
            except webbrowser.Error:
                print(f"Please navigate here: {auth_url}")
            
            # Wait for linking completion
            user_id = await link_state.wait_for_completion()
            return {
                "is_successful": bool(user_id),
                "user_id": user_id or primary_user_id
            }
        except Exception as error:
            print(f"Error during linking: {error}")
            return {
                "is_successful": False,
                "user_id": primary_user_id,
            }
    
    async def unlink(
        self,
        primary_user_id: str,
        connection: str,
        id_token: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Handle account linking flow.
        Args:
            primary_user_id: ID of the user initiating the link
            connection: Connection to link
            id_token: ID token of the primary user
            scope: OAuth scope
            **kwargs: Additional parameters for authorization
        Returns:
            Dict containing link status and user information
        """
        state = self._generate_state()
        link_state = LinkState(self.state_store, state)
        link_state.set_user(primary_user_id)

        auth_url = self.url_builder.get_authorize_url(
            state = state,
            scope = "unlink_account",
            audience = "my-account",
            requested_connection = connection,
            id_token_hint = id_token,
            client_id = self.client_id,
            redirect_uri = self.redirect_uri,
        )

        try:
            try:
                webbrowser.open(auth_url)
            except webbrowser.Error:
                print(f"Please navigate here: {auth_url}")
            
            # Wait for linking completion
            user_id = await link_state.wait_for_completion()
            return {
                "is_successful": bool(user_id),
                "user_id": user_id or primary_user_id
            }
        except Exception as error:
            print(f"Error during unlinking: {error}")
            return {
                "is_successful": False,
                "user_id": primary_user_id,
            }

    def get_session(self, user: User) -> Dict[str, Any]:
        """Get session for a user object"""
        return self.session_manager.get_session(user = user)

    
    def get_upstream_token(
        self,
        connection: str,
        refresh_token: str,
        additional_scopes: str | None = None
    ) -> Dict[str, Any]:
        """Get token for federated connection"""
        return self.token_manager.get_upstream_token(
            connection=connection,
            refresh_token=refresh_token,
            additional_scopes=additional_scopes
        )









