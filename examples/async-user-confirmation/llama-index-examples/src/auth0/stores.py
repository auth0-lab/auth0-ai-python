# flask_stores.py

from typing import Any, Dict, Optional, Union
from flask import Request, Response
from auth0_server_python.store.abstract import TransactionStore, StateStore
from auth0_server_python.auth_types import TransactionData, StateData


class FlaskCookieTransactionStore(TransactionStore):
    """
    A Flask-compatible transaction store that saves Auth0 transaction data
    in a signed, encrypted, HTTP-only cookie.
    """

    def __init__(self, secret: str, cookie_name: str = "_a0_tx"):
        # Initialize the abstract TransactionStore with the provided secret
        super().__init__({"secret": secret})
        self.cookie_name = cookie_name

    async def set(
        self,
        identifier: str,
        value: TransactionData,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        if not options or "response" not in options:
            raise ValueError(
                "Response object is required in store options for cookie storage.")
        response: Response = options["response"]
        # Encrypt the transaction data using the abstract store
        encrypted_value = self.encrypt(identifier, value.dict())
        # Store in a secure, HTTP-only cookie (short-lived)
        response.set_cookie(
            key=self.cookie_name,
            value=encrypted_value,
            path="/",
            samesite="Lax",
            secure=True,
            httponly=True,
            max_age=60,
        )

    async def get(
        self,
        identifier: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[TransactionData]:
        if not options or "request" not in options:
            raise ValueError(
                "Request object is required in store options for cookie storage.")
        request: Request = options["request"]
        encrypted_value = request.cookies.get(self.cookie_name)
        if not encrypted_value:
            return None
        try:
            # Decrypt and parse into TransactionData
            decrypted = self.decrypt(identifier, encrypted_value)
            return TransactionData.parse_obj(decrypted)
        except Exception:
            return None

    async def delete(
        self,
        identifier: str,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        if not options or "response" not in options:
            raise ValueError(
                "Response object is required in store options for cookie storage.")
        response: Response = options["response"]
        response.delete_cookie(key=self.cookie_name)


class FlaskStatelessStateStore(StateStore):
    """
    A Flask-compatible stateless state store that keeps session data
    encrypted directly in cookie chunks.
    """

    def __init__(
        self,
        secret: str,
        cookie_name: str = "_a0_session",
        expiration: int = 259200  # default 3 days
    ):
        super().__init__({"secret": secret})
        self.cookie_name = cookie_name
        self.expiration = expiration
        self.max_cookie_size = 4096
        self.cookie_options = {
            "httponly": True,
            "samesite": "Lax",
            "path": "/",
            "secure": True,
            "max_age": expiration,
        }

    async def set(
        self,
        identifier: str,
        state: Union[StateData, Dict[str, Any]],
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        if not options or "response" not in options:
            raise ValueError(
                "Response object is required in store options for stateless storage.")
        response: Response = options["response"]
        # Prepare plaintext dict
        state_dict = state.dict() if hasattr(
            state, 'dict') and callable(state.dict) else state
        # Encrypt entire state as one string
        encrypted_data = self.encrypt(identifier, state_dict)
        # Chunk into cookie-size pieces
        chunk_size = self.max_cookie_size - len(self.cookie_name) - 10
        for idx in range(0, len(encrypted_data), chunk_size):
            chunk_name = f"{self.cookie_name}_{idx // chunk_size}"
            chunk_value = encrypted_data[idx: idx + chunk_size]
            response.set_cookie(
                key=chunk_name,
                value=chunk_value,
                **self.cookie_options
            )

    async def get(
        self,
        identifier: str,
        options: Optional[Dict[str, Any]] = None
    ) -> Optional[Union[StateData, Dict[str, Any]]]:
        if not options or "request" not in options:
            raise ValueError(
                "Request object is required in store options for stateless storage.")
        request: Request = options["request"]
        # Collect all state cookie chunks
        parts = []
        for name, val in request.cookies.items():
            if name == self.cookie_name or name.startswith(f"{self.cookie_name}_"):
                try:
                    index = int(name.split("_")[-1]) if "_" in name else 0
                except ValueError:
                    continue
                parts.append((index, val))
        if not parts:
            return None
        parts.sort(key=lambda x: x[0])
        encrypted_full = "".join(chunk for _, chunk in parts)
        if not encrypted_full:
            return None
        try:
            # Decrypt and return raw dict or StateData
            decrypted = self.decrypt(identifier, encrypted_full)
            return StateData.parse_obj(decrypted)
        except Exception:
            return None

    async def delete(
        self,
        identifier: str,
        options: Optional[Dict[str, Any]] = None
    ) -> None:
        if not options or "response" not in options:
            raise ValueError(
                "Response object is required in store options for stateless storage.")
        response: Response = options["response"]
        # Remove base and chunk cookies (up to 20 chunks)
        response.delete_cookie(key=self.cookie_name)
        for i in range(20):
            response.delete_cookie(key=f"{self.cookie_name}_{i}")
