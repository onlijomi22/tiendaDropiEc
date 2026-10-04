"""Customer domain entities.

Spec: specs/customer/conversation.spec.md
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """WhatsApp message types."""
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"


class ConversationStatus(str, Enum):
    """Lifecycle status of a customer conversation."""
    OPEN = "OPEN"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"


class Message(BaseModel):
    """A single WhatsApp message.

    Spec: specs/customer/conversation.spec.md#message
    """

    id: str = Field(description="Unique message ID from WhatsApp")
    from_number: str = Field(description="Customer's WhatsApp number")
    body: str = Field(description="Message text content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    message_type: MessageType = Field(default=MessageType.TEXT)


class Conversation(BaseModel):
    """A conversation thread with a customer.

    Spec: specs/customer/conversation.spec.md#conversation
    Context window: last 10 messages per CA-CUST-03.
    """

    id: str = Field(description="Unique conversation ID")
    customer_number: str = Field(description="Customer WhatsApp number")
    messages: list[Message] = Field(default_factory=list)
    status: ConversationStatus = Field(default=ConversationStatus.OPEN)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    escalated_at: datetime | None = Field(default=None)

    # Spec CA-CUST-03: agent considers last 10 messages
    _CONTEXT_WINDOW: int = 10

    @property
    def context_messages(self) -> list[Message]:
        """Return last N messages for agent context (CA-CUST-03)."""
        return self.messages[-self._CONTEXT_WINDOW:]

    @property
    def agent_attempt_count(self) -> int:
        """Count how many times the agent has responded (for CA-CUST-02)."""
        return sum(1 for m in self.messages if m.from_number == "AGENT")
