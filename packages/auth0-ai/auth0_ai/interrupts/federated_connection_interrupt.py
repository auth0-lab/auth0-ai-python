from typing import Dict, Any
from .auth0_interrupt import Auth0Interrupt

class FederatedConnectionInterrupt(Auth0Interrupt):
    """
    Error thrown when a tool call requires an access token for an external service.

    Throw this error if the service returns Unauthorized for the current access token.
    """

    code = "FEDERATED_CONNECTION_ERROR"

    def __init__(self, message: str, connection: str, scopes: list[str], required_scopes: list[str]):
        """
        Initializes a FederatedConnectionInterrupt instance.

        Args:
            message (str): Error message describing the reason for the interrupt.
            connection (str): The Auth0 connection name.
            scopes (list[str]): The scopes required to access the external service as stated in the authorizer.
            required_scopes (list[str]): The union between the current scopes of the Access Token plus the required scopes.
                                         This is the list of scopes that will be used to request a new Access Token.
        """
        super().__init__(message, self.code)
        self.connection = connection
        self.scopes = scopes
        self.required_scopes = required_scopes

    def to_json(self) -> Dict[str, Any]:
        """
        Serializes the interrupt to a JSON object.
        """
        return {
            **super().to_json(),
            "connection": self.connection,
            "scopes": self.scopes,
            "requiredScopes": self.required_scopes,
        }


class FederatedConnectionError(Exception):
    """
    Error thrown when a tool call requires an access token for an external service.

    The authorizer will automatically convert this class of error to FederatedConnectionInterrupt.
    """

    def __init__(self, message: str):
        """
        Initializes a FederatedConnectionError instance.

        Args:
            message (str): Error message describing the reason for the error.
        """
        super().__init__(message)
