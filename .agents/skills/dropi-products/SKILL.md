---
name: dropi-products
description: Conocimiento experto para selección y análisis de productos en Dropi Ecuador. Incluye criterios de rentabilidad, métricas clave, y metodología de investigación de productos adaptada del curso de dropshipping 2026.
---

# Skill: Análisis y Selección de Productos Dropi

## Contexto
Dropi Ecuador es una plataforma de dropshipping con +160.000 productos y logística integrada.
A diferencia de AutoDS+Amazon, Dropi maneja el fulfillment localmente en Ecuador.

## Criterios de Selección de Productos (SPEC: CA-PROD-01/02/03)

### Margen mínimo requerido: 25% (gate) / 35% (objetivo)
```
Margen = (Precio_venta - Precio_Dropi) / Precio_venta × 100
```
- Menor a 25%: SKIP inmediato (CA-PROD-01)
- 25%-35%: Supera gate pero no alcanza margen objetivo. Analizar competencia
- Mayor a 35%: Producto candidato fuerte (alcanza margen objetivo)

### Stock mínimo: 10 unidades
- Menos de 10 unidades → nunca recomendar BUY aunque el margen sea excelente
- El stock bajo indica proveedor poco confiable o producto en discontinuación

### Score total (0-100):
| Rango | Recomendación |
|---|---|
| 70-100 | BUY ✅ |
| 40-69 | WATCH 👀 |
| 0-39 | SKIP ❌ |

## Metodología de Investigación de Productos

### Paso 1: Identificar nichos con demanda en Ecuador
Buscar en Dropi categorías con alta rotación:
- Hogar y decoración
- Belleza y cuidado personal
- Electrónica de consumo
- Ropa y accesorios
- Cocina y utensilios

### Paso 2: Filtros iniciales
1. Precio de venta sugerido: $15-$80 USD (punto dulce para Ecuador)
2. Margen bruto mínimo: 25% (gate), objetivo 35%
3. Stock disponible: mínimo 10 unidades
4. Proveedor con calificación ≥ 4 estrellas en Dropi
5. Producto con al menos 5 fotos de calidad

### Paso 3: Análisis de competencia
- Buscar el mismo producto en Marketplace Ecuador, OLX, Facebook Marketplace
- Si hay más de 20 vendedores activos → HIGH competition
- Si hay 5-20 vendedores → MEDIUM competition
- Si hay menos de 5 → LOW competition

### Paso 4: Análisis de tendencia
Fuentes para validar tendencia en Ecuador/Latam:
- Google Trends (filtrar por Ecuador)
- TikTok (buscar el producto, ver si hay videos virales)
- Grupos de Facebook de compradores Ecuador
- Temporadas: Navidad, Día de la Madre, Regreso a clases, San Valentín

### Paso 5: Scoring final
Usar AnalyzeProductUseCase con:
- competition_level: resultado del paso 3
- trend_score: 0.0-1.0 según paso 4

## Productos Ganadores en Dropi Ecuador (Patrones Comunes)

### Características de un producto ganador:
1. **Resuelve un problema**: No es solo decorativo, tiene utilidad práctica
2. **"Wow factor"**: Al verlo, el cliente piensa "¿cómo no tenía esto?"
3. **Difícil de encontrar localmente**: No disponible en tiendas físicas
4. **Precio justo para Ecuador**: $20-$60 USD es el rango óptimo
5. **Fácil de explicar en video**: Se muestra en 15-30 segundos en TikTok
6. **Margen de ganancia real**: Al menos $8-15 USD por venta después de costos

### Red flags (evitar):
- Electrónica compleja que puede fallar y generar devoluciones
- Ropa con tallas (problema de devoluciones por talla incorrecta)
- Productos que requieren instalación especializada
- Artículos frágiles sin empaque protegido en Dropi
- Productos de temporada fuera de temporada

## Cálculo de Rentabilidad Real

```
Precio de venta:           $35.00
- Costo Dropi:             $18.00
- Envío estimado:          $ 6.00  (Servientrega EC)
- CPA estimado:            $ 8.00  (costo estimado de ads por venta)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ganancia neta por venta:   $ 3.00
```

## Herramienta: Navegación en Dropi (Playwright)

Para extraer productos del catálogo:
1. Login en https://app.dropi.ec con credenciales
2. Navegar a Catálogo → Categoría deseada
3. Extraer: nombre, precio, stock, proveedor, imágenes, descripción
4. Mantener sesión activa (no re-login en cada consulta)
5. Usar `dropi_browser.py` (singleton) para reutilizar sesión
