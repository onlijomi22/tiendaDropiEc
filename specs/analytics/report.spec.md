# Spec: Dominio Analytics

## Propósito
Generar reportes de ventas, detectar anomalías y proveer insights accionables
al operador del negocio.

## Entidades

### SalesReport
| Campo | Tipo | Descripción |
|---|---|---|
| period_start | date | Inicio del período |
| period_end | date | Fin del período |
| total_orders | int | Total de pedidos |
| delivered_orders | int | Pedidos entregados |
| cancelled_orders | int | Pedidos cancelados |
| gross_revenue | float | Ingresos brutos (USD) |
| net_profit | float | Ganancia neta (USD) |
| delivery_rate | float | % entrega exitosa |
| top_products | list[str] | IDs productos más vendidos |

### Anomaly
| Campo | Tipo | Descripción |
|---|---|---|
| type | Enum(DROP/SPIKE/STALE) | Tipo de anomalía |
| metric | str | Métrica afectada |
| value | float | Valor actual |
| expected_value | float | Valor esperado |
| severity | Enum(LOW/MED/HIGH) | Severidad |
| detected_at | datetime | Cuándo se detectó |

## Criterios de Aceptación

### CA-ANAL-01: Reporte diario
- **Dado** datos de ventas del día anterior en Dropi
- **Cuando** el agente genera el reporte diario
- **Entonces** incluye todos los campos de SalesReport
- **Y** el delivery_rate se calcula como delivered/total_orders

### CA-ANAL-02: Detección de anomalía
- **Dado** una caída de pedidos > 30% respecto al promedio de 7 días
- **Cuando** el agente detecta la anomalía
- **Entonces** crea una Anomaly con severity HIGH
- **Y** notifica al operador por WhatsApp
