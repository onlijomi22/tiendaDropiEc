# Spec: Dominio Productos

## Propósito
El sistema debe ser capaz de analizar, puntuar y seleccionar productos del catálogo
de Dropi Ecuador para identificar los más rentables para vender con dropshipping.

## Entidades

### Product
| Campo | Tipo | Requerido | Descripción |
|---|---|---|---|
| id | str | ✅ | ID único del producto en Dropi |
| name | str | ✅ | Nombre del producto |
| category | str | ✅ | Categoría en Dropi |
| dropi_price | float | ✅ | Precio de costo en Dropi |
| suggested_price | float | ✅ | Precio sugerido de venta |
| stock | int | ✅ | Unidades disponibles |
| supplier_id | str | ✅ | ID del proveedor |
| images | list[str] | ✅ | URLs de imágenes |
| description | str | ✅ | Descripción del producto |
| weight_kg | float | ❌ | Peso para cálculo de envío |
| tags | list[str] | ❌ | Etiquetas del producto |

### ProductScore
| Campo | Tipo | Descripción |
|---|---|---|
| product_id | str | Referencia al producto |
| margin_pct | float | Margen bruto % |
| competition_level | Enum(LOW/MED/HIGH) | Nivel de competencia |
| trend_score | float | 0.0-1.0, tendencia del producto |
| total_score | float | Puntuación final 0-100 |
| recommendation | Enum(BUY/SKIP/WATCH) | Recomendación del agente |
| reasoning | str | Explicación del agente IA |

## Criterios de Aceptación

### CA-PROD-01: Análisis de margen
- **Dado** un producto con precio Dropi y precio sugerido de venta
- **Cuando** se calcula el margen
- **Entonces** el margen debe ser `(precio_venta - precio_dropi) / precio_venta * 100`
- **Y** si el margen es menor a 25%, la recomendación debe ser SKIP

### CA-PROD-02: Puntuación total
- **Dado** un ProductScore calculado
- **Cuando** se evalúa el score total
- **Entonces** el score total debe estar entre 0 y 100
- **Y** un score >= 70 genera recomendación BUY
- **Y** un score entre 40-69 genera recomendación WATCH
- **Y** un score < 40 genera recomendación SKIP

### CA-PROD-03: Stock mínimo
- **Dado** un producto con stock
- **Cuando** se analiza disponibilidad
- **Entonces** productos con stock < 10 no deben ser recomendados como BUY

### CA-PROD-04: Extracción de catálogo Dropi
- **Dado** credenciales válidas de Dropi
- **Cuando** se solicita el catálogo de una categoría
- **Entonces** se retorna lista de Product con todos los campos requeridos
- **Y** la sesión de Playwright se reutiliza (no re-login en cada consulta)

## Reglas de Negocio
- Margen mínimo aceptable: **25%**
- Stock mínimo para recomendar: **10 unidades**
- Score BUY mínimo: **70/100**
- Máximo productos a analizar por ejecución: **50**
