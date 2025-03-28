from typing import Type, TypeVar, Dict, Any

T = TypeVar("T", bound="Auth0Interrupt")

class Auth0Interrupt(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code

    def to_json(self) -> Dict[str, Any]:
        """
        Serialize the interrupt to a JSON object.
        """
        return {
            key: value for key, value in self.__dict__.items()
        } | {"message": self.args[0]}

    @classmethod
    def is_interrupt(cls: Type[T], interrupt: Any) -> bool:
        """
        Checks if an interrupt is of a specific type asserting its data component.
        """
        return (
            isinstance(interrupt, dict) and
            interrupt.__class__.__name__ == "Auth0Interrupt" and
            (not hasattr(cls, "code") or interrupt.get("code") == getattr(cls, "code", None))
        )
