---
name: dropi-analytics
description: KPIs, métricas y análisis de rendimiento para dropshipping con Dropi Ecuador. Incluye interpretación de Dropi Wallet, señales de alerta, y reportes periódicos.
---

# Skill: Analytics y Métricas Dropi Ecuador

## Contexto
El negocio de dropshipping con Dropi Ecuador opera principalmente con
**pago contra entrega**, lo que implica métricas únicas:
- La tasa de entrega es CRÍTICA (afecta directamente las ganancias)
- Los pedidos cancelados o no entregados son el principal riesgo
- El tiempo de entrega impacta la satisfacción y las reseñas

## KPIs Principales (Spec: CA-ANAL-01)

### Métricas de Pedidos
| KPI | Fórmula | Objetivo |
|---|---|---|
| Tasa de entrega | delivered / total × 100 | > 85% |
| Tasa de cancelación | cancelled / total × 100 | < 10% |
| Pedidos diarios | COUNT(orders WHERE date = hoy) | Objetivo mensual / 30 |
| Ticket promedio | gross_revenue / total_orders | > $30 USD |

### Métricas Financieras
| KPI | Fórmula | Objetivo |
|---|---|---|
| Ganancia neta | revenue - dropi_cost - ads_spend | > 0 siempre |
| Margen neto | net_profit / revenue × 100 | > 20% |
| ROAS general | revenue / ads_spend | > 3.0 |
| ROI mensual | net_profit / total_investment × 100 | > 50% |

### Métricas de Ads
| KPI | Fórmula | Objetivo |
|---|---|---|
| ROAS Google | conversions_value / spend | > 3.0 |
| ROAS TikTok | conversions_value / spend | > 2.5 |
| CPA (Costo por adquisición) | spend / conversions | < $8 USD |
| CTR Google | clicks / impressions × 100 | > 2% |
| CTR TikTok | clicks / impressions × 100 | > 1% |

## Detección de Anomalías (Spec: CA-ANAL-02)

### Umbral de alerta: caída de -30% vs promedio 7 días
```
Anomaly HIGH si:
(avg_7days - today_orders) / avg_7days × 100 >= 30%
```

### Tipos de anomalías y causas comunes:

| Anomalía | Posible causa | Acción |
|---|---|---|
| DROP en pedidos | Campaña pausada, producto agotado, temporada baja | Revisar stock y ads |
| DROP en tasa entrega | Problema logístico Dropi, zona conflictiva | Contactar soporte Dropi |
| SPIKE en pedidos | Campaña viral, temporada alta | Verificar stock |
| STALE (sin actividad) | Error en la tienda, ads no publicados | Revisar urgente |

## Reportes Periódicos

### Reporte Diario (ejecutar a las 8:00 AM)
```
📊 REPORTE DROPI - [FECHA]

Pedidos ayer:     X (▲/▼ vs promedio)
Entregados:       X (XX% tasa entrega)
Cancelados:       X (XX%)
Ingreso bruto:    $X
Gasto en ads:     $X
Ganancia neta:    $X

🏆 Top 3 productos:
1. [Producto] - X ventas
2. [Producto] - X ventas  
3. [Producto] - X ventas

⚠️ Alertas: [lista de anomalías]
```

### Reporte Semanal (lunes)
Resumen de 7 días con:
- Comparativa vs semana anterior
- Top productos de la semana
- ROAS por plataforma y campaña
- Predicción de la semana siguiente

### Reporte Mensual
- P&L completo (Ingresos - Costos Dropi - Ads = Ganancia)
- Análisis de tendencias
- Productos a discontinuar
- Oportunidades identificadas por el AnalyticsAgent

## Extracción de Datos desde Dropi (Playwright)

Para extraer reportes de ventas de Dropi:
1. Login en https://app.dropi.ec
2. Navegación: Mis ventas → Filtrar por fecha
3. Extraer: fecha, estado, precio, proveedor, ID pedido
4. Calcular KPIs localmente desde los datos extraídos
5. Fuente para ads metrics: Google Ads API + TikTok Ads API directamente

## Señales de Alerta por WhatsApp al Operador

El AnalyticsAgent debe notificar al operador si:
- Tasa de entrega < 70% en el día
- Caída de pedidos > 30% vs promedio
- ROAS de cualquier campaña < 1.5
- Stock de producto BUY < 5 unidades
- Gasto en ads > $50 sin conversiones en el día

Formato de alerta WhatsApp:
```
🚨 ALERTA TIENDA DROPI

[Tipo de alerta]
[Métrica afectada]: valor actual vs esperado
[Acción recomendada]

Revisa el dashboard para más detalles.
```
