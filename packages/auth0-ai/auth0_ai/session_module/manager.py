from __future__ import annotations
from typing import Any, Dict, Optional
import jwt
import time

from .storage.base_store import BaseStore
from .storage.local_store import LocalStore

class SessionManager:
    """
    Manages session operations including encryption, storage, and retrieval.
    Maintains exact compatibility with original implementation.
    """
    
    def __init__(
        self,
        auth_client: Any,
        use_local_cache: bool = True,
        get_ext_sessions=None,
        get_ext_session=None,
        set_ext_session=None,
        delete_ext_session=None,
        store: Optional[BaseStore] = None
    ):
        """
        Initialize session manager with original parameters plus optional store.
        
        Args:
            auth_client: Parent AIAuth instance
            use_local_cache: Whether to use local cache (default: True)
            get_ext_sessions: Optional custom get_sessions function
            get_ext_session: Optional custom get_session function
            set_ext_session: Optional custom set_session function
            delete_ext_session: Optional custom delete_session function
            store: Optional custom store implementation
        """
        self.auth_client = auth_client
        self.store = store or LocalStore(use_local_cache=use_local_cache)
        self.secret_key = auth_client.secret_key
        
        # Custom function handlers 
        self.get_ext_sessions = get_ext_sessions
        self.get_ext_session = get_ext_session
        self.set_ext_session = set_ext_session
        self.delete_ext_session = delete_ext_session

    # Original interface methods with exact same names and signatures
    def _get_stored_sessions(self) -> Any:
        """Get all stored session IDs"""
        if hasattr(self, 'get_ext_sessions') and self.get_ext_sessions:
            return self.get_ext_sessions()
        return self.store.get_stored_sessions()

    def _get_stored_session(self, user_id: str) -> str:
        """Get a specific stored session"""
        if hasattr(self, 'get_ext_session') and self.get_ext_session:
            return self.get_ext_session()
        return self.store.get_stored_session(user_id)

    def _set_stored_session(self, user_id: str, encrypted_session_data: str) -> None:
        """Store a session"""
        if hasattr(self, 'set_ext_session') and self.set_ext_session:
            self.set_ext_session()
        else:
            self.store.set_stored_session(user_id, encrypted_session_data)

    def _delete_stored_session(self, user_id: str) -> None:
        """Delete a stored session"""
        if hasattr(self, 'delete_ext_session') and self.delete_ext_session:
            self.delete_ext_session()
        else:
            self.store.delete_stored_session(user_id)

    # Session encryption and management methods (from original auth_client.py)
    async def set_encrypted_session(self, token_data: dict, state: str | None = None) -> str:
        """Create or update encrypted session"""
        id_token = token_data.get("id_token", "")
        if id_token:
            try:
                decoded_id_token = await self.auth_client.token_verifier.verify_signature(id_token)
                user_id = decoded_id_token.get("sub")
                if not user_id:
                    raise ValueError("ID token missing 'sub' claim.")
            except Exception as e:
                raise ValueError(f"Invalid ID token: {str(e)}")
        else:
            user_id = self.auth_client.state_store[state].get("user_id") if state else None

        existing_encrypted_session = self._get_stored_session(user_id)
        existing_linked_connections = {}
        existing_refresh_token = {}

        if existing_encrypted_session:
            existing_session = self.get_encrypted_session(user_id)
            existing_refresh_token = existing_session.get("tokens", {}).get("refresh_token", None)
            existing_linked_connections = existing_session.get("linked_connections")

        session_data = {
            "user_id": user_id,
            "tokens": self._get_token_set(token_data, existing_refresh_token),
            "linked_connections": self._get_linked_details(token_data, existing_linked_connections)
        }

        encrypted_session_data = jwt.encode(session_data, self.secret_key, algorithm="HS256")
        self._set_stored_session(user_id, encrypted_session_data)

        if state:
            self.auth_client.state_store[state] = {"user_id": user_id}

        return encrypted_session_data

    def get_encrypted_session(self, user_id: str) -> Dict[str, Any]:
        """Retrieve and decrypt session data"""
        encrypted_session = self._get_stored_session(user_id)
        
        if not encrypted_session:
            return {"not found"}

        try:
            decoded_data = jwt.decode(encrypted_session, self.secret_key, algorithms=["HS256"])
            
            token_expiry = decoded_data.get("tokens", {}).get("expires_at", {}).get("epoch")
            if token_expiry > int(time.time()):
                return decoded_data
            
            refresh_token = decoded_data.get("tokens", {}).get("refresh_token")
            if refresh_token:
                self._update_encrypted_session(user_id, refresh_token)
            else:
                self._delete_stored_session(user_id)
                return {"session expired"}

        except jwt.ExpiredSignatureError:
            return {"Session cookie has expired."}
        except jwt.InvalidTokenError:
            return {"Invalid session."}

    def _update_encrypted_session(self, user_id: str, refresh_token: str) -> None:
        """Update session with refreshed tokens"""
        token_manager = self.auth_client.token_manager
        updated_tokens = token_manager.refresh_token(refresh_token=refresh_token)
        if updated_tokens:
            self.set_encrypted_session(updated_tokens)


    def get_session_details(self, user_id: str) -> Dict[str, Any]:
        """Get session details for user"""
        if user_id in self._get_stored_sessions():
            return self.get_encrypted_session(user_id)
        return {"user_id not found in session store"}

    def get_session(self, user: Any) -> Dict[str, Any]:
        """Get session for user object"""
        if user.user_id in self._get_stored_sessions():
            return self.get_encrypted_session(user.user_id)
        return {"user_id not found in session store"}
    
    def _get_token_set(self, token_data: dict, existing_refresh_token: str | None = None) -> dict:
        """Format token data with expiry time"""
        return {
            "access_token": token_data.get("access_token"),
            "expires_at": {"epoch": int(time.time()) + token_data["expires_in"]},
            "refresh_token": token_data.get("refresh_token", existing_refresh_token),
            "id_token": token_data.get("id_token"),
            "scope": token_data.get("scope"),
        }

    def _get_linked_details(self, token_data: dict, existing_linked_connections: list[str] | None = None) -> list[str]:
        """Extract linked connections from token data"""
        linked_connections = set(existing_linked_connections or [])
        
        for item in token_data.get("authorization_details", []):
            if item.get("type") == "account_linking":
                link_with = item.get("linkParams", {}).get("link_with")
                if link_with:
                    linked_connections.add(link_with)
        
        return list(linked_connections)


    
