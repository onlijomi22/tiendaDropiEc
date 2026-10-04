"""Use case: Handle an incoming WhatsApp message.

Spec: specs/customer/conversation.spec.md
Criteria: CA-CUST-01, CA-CUST-02, CA-CUST-03
"""

from dataclasses import dataclass
from src.domain.business_rules import MAX_AGENT_ATTEMPTS, CONTEXT_WINDOW_MESSAGES
from src.domain.customer.entities import Message, MessageType
from src.domain.customer.repositories import ICustomerRepository
from src.infrastructure.ai.gemini_adapter import GeminiAdapter
from src.shared.logger import logger


@dataclass
class HandleMessageInput:
    """Input DTO: incoming WhatsApp message data."""
    message_id: str
    from_number: str
    body: str
    message_type: str = "TEXT"


@dataclass
class HandleMessageOutput:
    """Output DTO: agent response and conversation state."""
    reply: str
    escalated: bool = False
    conversation_id: str = ""


class HandleMessageUseCase:
    """Process an inbound WhatsApp message and generate a reply.

    Implements CA-CUST-01 (respond automatically),
    CA-CUST-02 (escalate after 3 failed attempts),
    CA-CUST-03 (context window of last 10 messages).

    Args:
        customer_repo: Repository for conversation management.
    """

    def __init__(self, customer_repo: ICustomerRepository, gemini_adapter: GeminiAdapter | None = None) -> None:
        self._repo = customer_repo
        self._gemini = gemini_adapter or GeminiAdapter()

    async def execute(self, input_data: HandleMessageInput) -> HandleMessageOutput:
        """Handle incoming message and return reply."""
        conversation = await self._repo.get_or_create_conversation(
            input_data.from_number
        )

        # Save incoming message
        message = Message(
            id=input_data.message_id,
            from_number=input_data.from_number,
            body=input_data.body,
            message_type=MessageType(input_data.message_type),
        )
        await self._repo.save_message(conversation.id, message)

        # Check if should escalate (CA-CUST-02)
        if conversation.agent_attempt_count >= MAX_AGENT_ATTEMPTS:
            await self._repo.update_status(conversation.id, "ESCALATED")
            escalation_msg = (
                "Un agente humano se comunicará contigo pronto. "
                "Gracias por tu paciencia. 🙏"
            )
            await self._repo.send_whatsapp_message(input_data.from_number, escalation_msg)
            logger.info(f"Conversation {conversation.id} escalated to human.")
            return HandleMessageOutput(
                reply=escalation_msg,
                escalated=True,
                conversation_id=conversation.id,
            )

        # Build context and generate reply (CA-CUST-03)
        context_history = [
            f"{m.from_number}: {m.body}" for m in conversation.context_messages
        ]
        reply = await self._generate_reply(input_data.body, context_history)

        # Save agent reply
        agent_message = Message(
            id=f"agent_{input_data.message_id}",
            from_number="AGENT",
            body=reply,
        )
        await self._repo.save_message(conversation.id, agent_message)
        await self._repo.send_whatsapp_message(input_data.from_number, reply)

        logger.info(f"Replied to {input_data.from_number}: {reply[:50]}...")
        return HandleMessageOutput(reply=reply, conversation_id=conversation.id)

    async def _generate_reply(self, message: str, history: list[str]) -> str:
        """Generate a customer service reply using Gemini."""
        history_text = "\n".join(history[-CONTEXT_WINDOW_MESSAGES:])  # CA-CUST-03
        prompt = (
            "Eres un agente de atencion al cliente de una tienda dropshipping en Ecuador.\n"
            "Se amable, conciso y resuelve la consulta del cliente en espanol.\n"
            f"Historial de conversacion:\n{history_text}\n\n"
            f"Nuevo mensaje del cliente: {message}\n\n"
            "Responde directamente sin saludos innecesarios:"
        )
        text = await self._gemini.generate(prompt)
        return text.strip()
