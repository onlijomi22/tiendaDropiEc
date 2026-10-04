"""WhatsApp Business Cloud API client.

Sends messages via Meta's Cloud API.
Docs: https://developers.facebook.com/docs/whatsapp/cloud-api

Spec: specs/customer/conversation.spec.md
"""

import httpx
from src.shared.config import get_whatsapp_settings
from src.shared.exceptions import WhatsAppAPIError
from src.shared.logger import logger

_META_API_VERSION = "v18.0"
_META_API_BASE = "https://graph.facebook.com"


class WhatsAppClient:
    """HTTP client for Meta WhatsApp Business Cloud API.

    Handles:
    - Sending text messages (CA-CUST-01)
    - Webhook payload validation

    Args:
        settings: WhatsApp API credentials (auto-loaded from env).
    """

    def __init__(self) -> None:
        self._settings = get_whatsapp_settings()
        self._base_url = (
            f"{_META_API_BASE}/{_META_API_VERSION}/"
            f"{self._settings.phone_number_id}/messages"
        )

    async def send_text(
        self, to: str, body: str
    ) -> str:
        """Send a text message to a WhatsApp number.

        Args:
            to: Recipient WhatsApp number (E.164 format, e.g. +593991234567).
            body: Message text to send.

        Returns:
            WhatsApp message ID of the sent message.

        Raises:
            WhatsAppAPIError: If the API call fails.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": body},
        }
        headers = {
            "Authorization": f"Bearer {self._settings.access_token.get_secret_value()}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            try:
                response = await client.post(
                    self._base_url, json=payload, headers=headers
                )
                response.raise_for_status()
                data = response.json()
                message_id = data["messages"][0]["id"]
                logger.info(f"WhatsApp message sent to {to}: {message_id}")
                return message_id
            except httpx.HTTPStatusError as e:
                raise WhatsAppAPIError(
                    f"Meta API error {e.response.status_code}: {e.response.text}"
                ) from e
            except Exception as e:
                raise WhatsAppAPIError(f"Failed to send WhatsApp message: {e}") from e
