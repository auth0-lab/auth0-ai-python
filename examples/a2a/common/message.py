from dataclasses import dataclass
import time
from typing import Dict, Any
import uuid

@dataclass
class Message:
    id: str
    sender: str
    recipient: str
    timestamp: str
    query_type: str
    payload: Dict[str, Any]

    @staticmethod
    def create(sender: str, recipient: str, query_type: str, payload: Dict[str, Any]) -> 'Message':
        return Message(
            id=str(uuid.uuid4()),
            sender=sender,
            recipient=recipient,
            timestamp=time.time().isoformat() + "Z",
            query_type=query_type,
            payload=payload
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sender": self.sender,
            "recipient": self.recipient,
            "timestamp": self.timestamp,
            "query_type": self.query_type,
            "payload": self.payload,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Message':
        required_fields = ["id", "sender", "recipient", "timestamp", "query_type", "payload"]
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(f"Missing fields in message: {missing}")

        return Message(
            id=data["id"],
            sender=data["sender"],
            recipient=data["recipient"],
            timestamp=data["timestamp"],
            query_type=data["query_type"],
            payload=data["payload"]
        )
