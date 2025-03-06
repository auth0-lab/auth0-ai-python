from typing import TypedDict

class Auth0StateType(TypedDict):
    error: str

class Auth0State(TypedDict):
    auth0: Auth0StateType
    task_id: str