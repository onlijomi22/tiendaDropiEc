"""Customer repository interface.

Spec: specs/customer/conversation.spec.md
"""

from abc import ABC, abstractmethod
from src.domain.customer.entities import Conversation, Message


class ICustomerRepository(ABC):
    """Abstract repository for customer conversation management."""

    @abstractmethod
    async def get_or_create_conversation(self, customer_number: str) -> Conversation:
        """Get existing open conversation or create a new one.

        Args:
            customer_number: WhatsApp number of the customer.

        Returns:
            Existing open Conversation or a new Conversation.
        """

    @abstractmethod
    async def save_message(self, conversation_id: str, message: Message) -> None:
        """Persist a new message to a conversation.

        Args:
            conversation_id: Target conversation ID.
            message: Message to save.
        """

    @abstractmethod
    async def update_status(
        self, conversation_id: str, status: str
    ) -> None:
        """Update conversation status (OPEN/ESCALATED/RESOLVED).

        Args:
            conversation_id: Conversation to update.
            status: New status string.
        """

    @abstractmethod
    async def send_whatsapp_message(
        self, to_number: str, body: str
    ) -> str:
        """Send a message via WhatsApp Business API.

        Args:
            to_number: Recipient WhatsApp number.
            body: Message text to send.

        Returns:
            WhatsApp message ID of the sent message.

        Raises:
            WhatsAppAPIError: If the Meta API call fails.
        """
