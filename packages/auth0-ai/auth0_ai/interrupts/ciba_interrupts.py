from abc import ABC
from typing import Any, Type, TypeVar
from auth0_ai.interrupts.auth0_interrupt import Auth0Interrupt
from auth0_ai.authorizers.ciba import CIBAAuthorizationRequest

class WithRequestData:
    def __init__(self, request: CIBAAuthorizationRequest):
        super().__init__()
        self._request = request

    @property
    def request(self) -> CIBAAuthorizationRequest:
        return self._request

CIBAInterruptType = TypeVar("T", bound="CIBAInterrupt")

class CIBAInterrupt(Auth0Interrupt, ABC):
    def __init__(self, message: str, code: str):
        super().__init__(message, code)

    @classmethod
    def is_interrupt(cls: Type[CIBAInterruptType], interrupt: Any) -> bool:
        return (
            interrupt
            and Auth0Interrupt.is_interrupt(interrupt)
            and isinstance(interrupt.get("code"), str)
            and interrupt["code"].startswith("CIBA_")
        )

    @classmethod
    def has_request_data(cls, interrupt: Any) -> bool:
        return (
        cls.is_interrupt(interrupt)
        and isinstance(interrupt, WithRequestData)
    )


class AccessDeniedInterrupt(CIBAInterrupt, WithRequestData):
    code: str = "CIBA_ACCESS_DENIED"

    def __init__(self, message: str, request: CIBAAuthorizationRequest):
        CIBAInterrupt.__init__(self, message, AccessDeniedInterrupt.code)
        WithRequestData.__init__(self, request)


class UserDoesNotHavePushNotificationsInterrupt(CIBAInterrupt):
    code: str = "CIBA_USER_DOES_NOT_HAVE_PUSH_NOTIFICATIONS"

    def __init__(self, message: str):
        super().__init__(message, UserDoesNotHavePushNotificationsInterrupt.code)


class AuthorizationRequestExpiredInterrupt(CIBAInterrupt, WithRequestData):
    code: str = "CIBA_AUTHORIZATION_REQUEST_EXPIRED"

    def __init__(self, message: str, request: CIBAAuthorizationRequest):
        CIBAInterrupt.__init__(self, message, AuthorizationRequestExpiredInterrupt.code)
        WithRequestData.__init__(self, request)


class AuthorizationPendingInterrupt(CIBAInterrupt, WithRequestData):
    code: str = "CIBA_AUTHORIZATION_PENDING"

    def __init__(self, message: str, request: CIBAAuthorizationRequest):
        CIBAInterrupt.__init__(self, message, AuthorizationPendingInterrupt.code)
        WithRequestData.__init__(self, request)


class AuthorizationPollingInterrupt(Auth0Interrupt, WithRequestData):
    code: str = "CIBA_AUTHORIZATION_POLLING_ERROR"

    def __init__(self, message: str, request: CIBAAuthorizationRequest):
        Auth0Interrupt.__init__(self, message, AuthorizationPollingInterrupt.code)
        WithRequestData.__init__(self, request)


class InvalidGrantInterrupt(Auth0Interrupt, WithRequestData):
    code: str = "CIBA_INVALID_GRANT"

    def __init__(self, message: str, request: CIBAAuthorizationRequest):
        Auth0Interrupt.__init__(self, message, InvalidGrantInterrupt.code)
        WithRequestData.__init__(self, request)
