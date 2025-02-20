from __future__ import annotations
import time
from typing import Any, Dict, Optional
from .base_state import BaseState

class LinkState(BaseState):
    """
    Handles the state management for the account linking flow.
    """
    def __init__(self, state_store: Dict[str, Dict[str, Any]], state: str):
        """
        Initialize link state tracker.
        Args:
            state_store: Reference to the global state store
            state: Unique state identifier for this linking attempt
        """
        super().__init__(state_store, state)
        self.start_time = time.time()
        self.timeout = 60  # Linking timeout in seconds

    def is_completed(self) -> bool:
        """Check if linking flow is completed"""
        return self.state_store[self.state].get("is_completed", False)
    def get_user(self) -> str:
        """Get user information after linking completion"""
        return self.state_store.get(self.state, "login failed!").get("user_id")
    def set_user(self, user_id: str) -> None:
        """
        Set the primary user ID for linking.
        Args:
            user_id: ID of the user initiating the link
        """
        is_completed = self.state_store[self.state].get("is_completed", False)
        self.state_store[self.state] = {
            "is_completed": is_completed,
            "user_id": user_id
        }

    def complete(self, user_id: str) -> None:
        """
        Mark linking as complete with user information.
        Args:
            user_id: ID of the linked user
        """
        self.state_store[self.state] = {
            "user_id": user_id,
            "is_completed": True
        }

    async def wait_for_completion(self) -> Optional[str]:
        """
        Wait for linking completion or timeout.
        Returns:
            User ID if successful, None if timeout or failure
        """
        while not self.is_completed():
            if time.time() > self.start_time + self.timeout:
                self.terminate()
                return None
            await self._sleep(0.25)  # Small delay between checks
        user_id = self.get_user()
        self.terminate()
        if user_id == "login failed!":
            return None
        return user_id