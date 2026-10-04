# Spec: Dominio Atención al Cliente

## Propósito
Manejar conversaciones de clientes por WhatsApp Business de forma automática
mediante el CustomerSupportAgent, escalando a humano cuando sea necesario.

## Entidades

### Message
| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| id | str | ✅ | ID único del mensaje |
| from_number | str | ✅ | Número WhatsApp del cliente |
| body | str | ✅ | Contenido del mensaje |
| timestamp | datetime | ✅ | Fecha/hora del mensaje |
| message_type | Enum(TEXT/IMAGE/AUDIO) | ✅ | Tipo de mensaje |

### Conversation
| Campo | Tipo | Descripción |
|---|---|---|
| id | str | ID de conversación |
| customer_number | str | Número del cliente |
| messages | list[Message] | Historial |
| status | Enum(OPEN/ESCALATED/RESOLVED) | Estado |
| created_at | datetime | Inicio |
| escalated_at | datetime | Cuándo se escaló (si aplica) |

## Criterios de Aceptación

### CA-CUST-01: Respuesta automática
- **Dado** un mensaje entrante de WhatsApp
- **Cuando** el agente procesa el mensaje
- **Entonces** responde en menos de 30 segundos
- **Y** la respuesta es en español

### CA-CUST-02: Escalación
- **Dado** una conversación activa
- **Cuando** el agente no puede resolver en 3 intentos
- **Entonces** escala a humano y notifica con el historial completo

### CA-CUST-03: Contexto de conversación
- **Dado** un cliente que envía múltiples mensajes
- **Cuando** el agente responde
- **Entonces** tiene en cuenta los últimos 10 mensajes del historial
