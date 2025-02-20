from __future__ import annotations
import shelve
import os
from typing import List

from .base_store import BaseStore

class LocalStore(BaseStore):
    """
    Local storage implementation using Python's shelve module.
    This is the default storage mechanism, maintaining the original implementation's behavior.
    """
    
    def __init__(self, file_path: str = ".sessions_cache", use_local_cache: bool = True):
        """
        Initialize local store.
        
        Args:
            file_path: Path to the shelve file (default: ".sessions_cache")
            use_local_cache: Flag to determine if local cache should be used (default: True)
        """
        self.file_path = file_path
        self.use_local_cache = use_local_cache or os.environ.get("AUTH0_USE_LOCAL_CACHE", True)

    def get_stored_sessions(self) -> List[str]:
        """Get all stored session IDs"""
        if self.use_local_cache:
            with shelve.open(self.file_path) as sessions:
                return list(sessions.keys())
        return []

    def get_stored_session(self, user_id: str) -> str | None:
        """Get a specific stored session"""
        if self.use_local_cache:
            with shelve.open(self.file_path) as sessions:
                return sessions.get(user_id)
        return None

    def set_stored_session(self, user_id: str, encrypted_session_data: str) -> None:
        """Store a session"""
        if self.use_local_cache:
            with shelve.open(self.file_path) as sessions:
                sessions[user_id] = encrypted_session_data
                sessions.sync()

    def delete_stored_session(self, user_id: str) -> None:
        """Delete a stored session"""
        if self.use_local_cache:
            with shelve.open(self.file_path) as sessions:
                if user_id in sessions:
                    del sessions[user_id]
