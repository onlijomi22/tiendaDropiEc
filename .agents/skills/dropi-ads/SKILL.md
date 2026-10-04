---
name: dropi-ads
description: Estrategia de publicidad pagada (Google Ads + TikTok Ads) adaptada para dropshipping con Dropi Ecuador. Incluye estructura de campañas, presupuestos, ROAS objetivo y generación de copy.
---

# Skill: Gestión de Campañas Publicitarias Dropi

## Contexto
Estrategia adaptada del curso de dropshipping 2026 (originalmente para Amazon+AutoDS)
al contexto de Dropi Ecuador: pago contra entrega, mercado Latam, precios en USD.

## ROAS Objetivos (Spec: CA-ADS-02/03)

| Métrica | Valor objetivo |
|---|---|
| ROAS mínimo aceptable | 2.0 |
| ROAS para escalar presupuesto | 3.0 |
| ROAS ideal (campaña madura) | 4.0-6.0 |
| Días antes de pausar por ROAS bajo | 3 días consecutivos |

## Estructura de Presupuestos

### Fase 1 — Testing (días 1-5): $5/día
- Objetivo: validar que el producto convierte
- Si ROAS < 2.0 en 3 días → PAUSAR (CA-ADS-02)
- Si ROAS > 3.0 en 5 días → ESCALAR

### Fase 2 — Escalado (días 6+): $15/día
- Aumentar solo si ROAS > 3.0 (CA-ADS-03)
- Escalar gradualmente: +50% de presupuesto por semana máximo

### Fase 3 — Optimización: presupuesto variable
- Multiplicar el presupuesto de los ad sets ganadores
- Pausar lo que no convierte

## Google Ads para Dropi Ecuador

### Tipo de campaña recomendado: Performance Max
- Conecta Shopping + Search + Display automáticamente
- Ideal para dropshipping con catálogo Dropi
- Requiere: feed de productos o URL de la tienda

### Estructura básica:
```
Campaña: [Producto] - Ecuador - PM
  └── Grupo de activos 1: Producto principal
        ├── Headlines (máx 30 chars): 3-5 variaciones
        ├── Descriptions (máx 90 chars): 2-3 variaciones
        ├── Imágenes: mínimo 3 (1:1, 4:1, 1.91:1)
        └── CTA: Compra Ahora / Ver Oferta
```

### Copy efectivo para Ecuador (CA-ADS-01):
- **Headline ejemplos** (máx 30 chars):
  - "Envío gratis Ecuador 🚚"
  - "Pago contraentrega ✅"
  - "Oferta limitada - Hoy"
- **Description ejemplos** (máx 90 chars):
  - "Entrega en 24-48h a todo Ecuador. Sin tarjeta. Paga cuando recibas tu pedido."

### Targeting Ecuador:
- Ubicación: Ecuador (todas las ciudades)
- Idioma: Español
- Puja: Maximizar conversiones (fase testing) → ROAS objetivo (fase escala)

## TikTok Ads para Dropi Ecuador

### Por qué TikTok funciona para Dropi Ecuador:
- El público es joven (18-34) con alto poder de compra en Ecuador
- Los productos con "wow factor" se viralizan orgánicamente
- Costo por clic más bajo que Google en Ecuador
- Pago contra entrega es un CTA muy efectivo en TikTok

### Tipo de campaña recomendado: Video Shopping Ads
- Muestra el producto en uso
- Video: 15-30 segundos máximo
- Los primeros 3 segundos son críticos (hook)

### Estructura de hook efectivo (primeros 3 segundos):
```
Opción 1: Problema → Solución
"¿Cansado de [problema]? Este producto cambia todo..."

Opción 2: Resultado sorprendente
[Mostrar el producto funcionando sin explicación]

Opción 3: Pregunta retórica
"¿Sabías que puedes [beneficio] por solo $X?"
```

### Copy TikTok Ads (Headline máx 100 chars):
- "Este producto está agotando stocks en Ecuador 🇪🇨"
- "Paga cuando lo recibas - Envío gratis Ecuador"
- "Por menos de $30: el gadget que todos quieren"

## Reglas de Optimización Automática

### Pausar automáticamente si:
- ROAS < 2.0 por 3 días consecutivos (CA-ADS-02)
- CTR < 0.5% en Google o < 1% en TikTok después de 3 días
- Gasto > $30 sin ninguna conversión

### Escalar automáticamente si:
- ROAS > 3.0 por 5 días consecutivos (CA-ADS-03)
- CPM estable o bajando
- Conversion rate > 2%

## Generación de Copy con Gemini

El agente genera copy usando:
- Nombre del producto
- Descripción (primeros 200 chars)
- Precio de venta
- Restricciones de caracteres por plataforma

El copy siempre menciona:
1. "Ecuador" o símbolo 🇪🇨 (localización)
2. "Pago contra entrega" o "Paga cuando recibas" (diferenciador Dropi)
3. Una urgencia genuina si aplica
