from __future__ import annotations
import asyncio
from typing import Any, Dict
from abc import ABC, abstractmethod

class BaseState(ABC):
    """
    Base class for state management in authentication flows.
    """
    def __init__(self, state_store: Dict[str, Dict[str, Any]], state: str):
        """
        Initialize base state tracker.
        Args:
            state_store: Reference to the global state store
            state: Unique state identifier for this flow
        """
        self.state_store = state_store
        self.state = state

    @abstractmethod
    def is_completed(self) -> bool:
        """Check if flow is completed"""
        pass
    @abstractmethod
    def get_user(self) -> Any:
        """Get user information after flow completion"""
        pass
    @abstractmethod
    def complete(self, user_id: str) -> None:
        """Mark flow as complete with user information"""
        pass
    def terminate(self) -> None:
        """Clean up state data"""
        if self.state in self.state_store:
            del self.state_store[self.state]
    async def _sleep(self, seconds: float) -> None:
        """Async sleep helper"""
        await asyncio.sleep(seconds)