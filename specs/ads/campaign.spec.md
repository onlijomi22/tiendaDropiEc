# Spec: Dominio Campañas Publicitarias

## Propósito
Gestionar y optimizar campañas en Google Ads y TikTok Ads para productos
seleccionados por el ProductAnalystAgent.

## Entidades

### Campaign
| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| id | str | ✅ | ID de campaña en plataforma |
| platform | Enum(GOOGLE/TIKTOK) | ✅ | Plataforma publicitaria |
| product_id | str | ✅ | Producto anunciado |
| name | str | ✅ | Nombre de la campaña |
| daily_budget_usd | float | ✅ | Presupuesto diario |
| status | Enum(ACTIVE/PAUSED/ENDED) | ✅ | Estado |
| created_at | datetime | ✅ | Fecha de creación |

### AdCopy
| Campo | Tipo | Descripción |
|---|---|---|
| headline | str | Título principal (max 30 chars Google, 100 TikTok) |
| description | str | Descripción (max 90 chars Google) |
| call_to_action | str | CTA (Compra Ahora, Ver Más, etc.) |
| platform | Enum(GOOGLE/TIKTOK) | Plataforma destino |

### CampaignMetrics
| Campo | Tipo | Descripción |
|---|---|---|
| campaign_id | str | Referencia a Campaign |
| impressions | int | Impresiones |
| clicks | int | Clics |
| conversions | int | Conversiones |
| spend_usd | float | Gasto total |
| roas | float | Return on Ad Spend |
| period_days | int | Período de las métricas |

## Criterios de Aceptación

### CA-ADS-01: Generación de copy
- **Dado** un Product con name y description
- **Cuando** el agente genera AdCopy para Google
- **Entonces** el headline no supera 30 caracteres
- **Y** la description no supera 90 caracteres
- **Y** el copy está en español latinoamericano

### CA-ADS-02: ROAS mínimo
- **Dado** métricas de una campaña activa
- **Cuando** el ROAS < 2.0 por 3 días consecutivos
- **Entonces** la campaña debe ser pausada automáticamente

### CA-ADS-03: Presupuesto inicial
- **Dado** un producto con recommendation BUY
- **Cuando** se crea una campaña nueva
- **Entonces** el presupuesto diario inicial es $5 USD
- **Y** se escala a $15 USD si ROAS > 3.0 después de 5 días
