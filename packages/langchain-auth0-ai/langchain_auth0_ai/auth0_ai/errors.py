class AccessDeniedError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class UserDoesNotHavePushNotificationsError(Exception):
    def __init__(self, message: str):
        super().__init__(message)

class AuthorizationRequestExpiredError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
