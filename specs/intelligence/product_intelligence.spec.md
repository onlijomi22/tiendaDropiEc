# Spec: Product Intelligence Domain

## Propósito
Enriquecer datos de productos de Dropi con información real del mercado ecuatoriano:
competencia en MercadoLibre, insights reales de compradores, tendencias.

NO inventar datos. Toda información proviene de búsquedas web reales.

## Entidades

### CompetitorListing
| Campo | Tipo | Descripción |
|---|---|---|
| title | str | Nombre del listing en ML |
| price_usd | float | Precio de venta |
| sales_count | int | Número de ventas |
| rating | float | Calificación 0-5 |
| url | str | URL del listing |

### MarketInsight
| Campo | Tipo | Descripción |
|---|---|---|
| category | str | Categoría del producto |
| buyer_concerns | list[str] | Preocupaciones REALES de compradores |
| buyer_positives | list[str] | Lo que REALMENTE valoran |
| avg_competitor_price | float | Precio promedio de competencia |
| competition_count | int | Número de competidores encontrados |
| competition_level | Enum(LOW/MED/HIGH) | Nivel competencia |
| sources | list[str] | URLs fuente de los insights |

### ProductCopyDraft
| Campo | Tipo | Descripción |
|---|---|---|
| product_id | str | ID del producto Dropi |
| landing_headline | str | Título principal de landing (max 60 chars) |
| landing_subheadline | str | Subtítulo (max 120 chars) |
| benefits | list[str] | 3-5 beneficios basados en datos reales |
| review_quotes | list[str] | 2-3 frases tipo reseña basadas en datos reales |
| objection_handlers | list[str] | Respuestas a miedos reales de compradores |
| tiktok_hook | str | Primera frase del video (los primeros 3 segundos) |
| tiktok_script | str | Guión completo 30 segundos |
| meta_headline | str | Headline para Meta Ads (max 40 chars) |
| meta_body | str | Texto Meta Ads (max 125 chars) |
| suggested_price_usd | float | Precio sugerido basado en competencia + margen |
| data_sources | list[str] | Fuentes usadas (para transparencia) |
| human_review_notes | str | Notas para que el humano revise/edite |

## Criterios de Aceptación

### CA-INTEL-01: Datos reales siempre
- Todo buyer_concerns y buyer_positives debe tener fuente URL
- Nunca generar reseñas completamente inventadas
- Si no hay datos suficientes → decirlo explícitamente

### CA-INTEL-02: Competencia MercadoLibre
- Buscar el producto en mercadolibre.com.ec
- Extraer al menos 3 listings de competencia
- Calcular precio promedio de competencia

### CA-INTEL-03: Copy dual
- Siempre mostrar datos crudos (MarketInsight)
- Siempre generar borrador de copy (ProductCopyDraft)
- El borrador incluye nota human_review_notes con qué validar
