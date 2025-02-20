from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List

class BaseStore(ABC):
    """
    Abstract base class defining the interface for session storage implementations.
    All storage implementations must inherit from this class and implement
    all abstract methods.
    """
    @abstractmethod
    def get_stored_sessions(self) -> List[str]:
        """
        Get all stored session IDs.
        Returns:
            List of session IDs
        """
        pass
    @abstractmethod
    def get_stored_session(self, user_id: str) -> str | None:
        """
        Get a specific stored session.
        Args:
            user_id: The ID of the user whose session to retrieve
        Returns:
            The session data if found, None otherwise
        """
        pass
    @abstractmethod
    def set_stored_session(self, user_id: str, encrypted_session_data: str) -> None:
        """
        Store a session.
        Args:
            user_id: The ID of the user whose session to store
            encrypted_session_data: The encrypted session data to store
        """
        pass
    @abstractmethod
    def delete_stored_session(self, user_id: str) -> None:
        """
        Delete a stored session.
        Args:
            user_id: The ID of the user whose session to delete
        """
        pass