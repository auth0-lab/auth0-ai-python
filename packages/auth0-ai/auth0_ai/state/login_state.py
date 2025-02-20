from __future__ import annotations
import time
from typing import Any, Dict, Optional

from .base_state import BaseState

class LoginState(BaseState):
    """
    Handles the state management for the login flow.
    """
    
    def __init__(self, state_store: Dict[str, Dict[str, Any]], state: str):
        """
        Initialize login state tracker.
        
        Args:
            state_store: Reference to the global state store
            state: Unique state identifier for this login attempt
        """
        super().__init__(state_store, state)
        self.start_time = time.time()
        self.timeout = 60  # Login timeout in seconds

    def is_completed(self) -> bool:
        """Check if login flow is completed"""
        return self.state_store[self.state].get("is_completed", False)

    def get_user(self) -> str | Dict[str, Any]:
        """Get user information after login completion"""
        return self.state_store.get(self.state, "login failed!")

    def complete(self, user_id: str) -> None:
        """
        Mark login as complete with user information.
        
        Args:
            user_id: ID of the authenticated user
        """
        self.state_store[self.state] = {
            "user_id": user_id,
            "is_completed": True
        }

    async def wait_for_completion(self) -> Optional[str]:
        """
        Wait for login completion or timeout.
        
        Returns:
            User ID if successful, None if timeout or failure
        """
        while not self.is_completed():
            if time.time() > self.start_time + self.timeout:
                self.terminate()
                return None
            await self._sleep(0.25)  # Small delay between checks

        user_data = self.get_user()
        self.terminate()
        
        if user_data == "login failed!":
            return None
            
        return user_data.get("user_id")