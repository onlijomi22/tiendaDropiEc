# Architecture

## 1. Objetivo

La arquitectura debe permitir evolucionar TiendaDropiEc desde una solución específica para Dropi hacia una plataforma de AI Commerce reutilizable para múltiples proveedores y países.

---

## 2. Principio principal

> El dominio de negocio no debe depender de proveedores externos.

Dropi, WhatsApp, Meta, NotebookLM y cualquier LLM deben considerarse integraciones reemplazables.

---

## 3. Capas propuestas

```text
Frontend
   ↓
Application
   ↓
Domain
   ↓
Ports / Interfaces
   ↓
Adapters
   ↓
External Services
```

---

## 4. Estructura sugerida

```text
TiendaDropiEc/
│
├── .agents/
│   └── skills/
│       ├── core/
│       │   ├── orchestrator/
│       │   └── prompt-engineering/
│       │
│       ├── commerce/
│       │   ├── dropi-products/
│       │   ├── product-economics/
│       │   ├── market-research/
│       │   ├── customer/
│       │   ├── orders/
│       │   └── analytics/
│       │
│       └── marketing/
│           ├── landing-pages/
│           ├── creative-intelligence/
│           ├── viral-intelligence/
│           └── ads/
│
├── src/
│   ├── domain/
│   ├── application/
│   ├── integrations/
│   │   ├── dropi/
│   │   ├── whatsapp/
│   │   ├── meta/
│   │   ├── notebooklm/
│   │   └── llm/
│   └── infrastructure/
│
├── frontend/
├── tests/
├── scripts/
├── data/
│
├── PROJECT.md
├── CLAUDE.md
├── ARCHITECTURE.md
└── DECISIONS.md
```

Esta estructura es un objetivo arquitectónico. No debe aplicarse mediante un refactor masivo si el proyecto actual funciona.

La migración debe ser incremental.

---

## 5. Domain

Debe contener lógica de negocio independiente.

Ejemplos:

- Product
- Supplier
- ProductEconomics
- ProductScore
- CampaignMetrics
- Order
- Customer
- ProductStatus

No debe importar librerías específicas de APIs externas.

---

## 6. Application

Debe contener casos de uso.

Ejemplos:

```text
DiscoverProducts
AnalyzeProduct
CalculateEconomics
ResearchMarket
ScoreProduct
CreateLanding
GenerateCreative
CreateOrder
AnalyzeCampaign
```

---

## 7. Integrations

Contiene adapters de servicios externos.

Ejemplo:

```text
integrations/dropi/
integrations/whatsapp/
integrations/meta/
integrations/notebooklm/
integrations/llm/
```

---

## 8. Provider abstraction

Ejemplo conceptual:

```python
class ProductProvider:
    def search_products(self, query):
        raise NotImplementedError
```

Adapter:

```python
class DropiProductProvider(ProductProvider):
    ...
```

En el futuro:

```python
class AnotherProvider(ProductProvider):
    ...
```

---

## 9. Product Intelligence

El motor de selección debe separar:

### Datos del proveedor

- costo;
- stock;
- proveedor;
- rating;
- imágenes;
- categoría.

### Datos de mercado

- competencia;
- tendencia;
- precio;
- demanda;
- saturación.

### Economía

- margen bruto;
- contribución;
- break-even CPA;
- expected profit.

### Creatividad

- capacidad de demostración;
- problemas que resuelve;
- variedad de ángulos;
- potencial visual.

---

## 10. Product Score

El score debe ser configurable.

Ejemplo inicial:

```text
Profitability       30%
Demand              20%
Creative potential  15%
Competition         10%
Supplier quality    10%
Delivery history    10%
Trend                5%
```

Estos valores NO son definitivos.

Deben poder modificarse mediante configuración y más adelante calibrarse con datos reales.

---

## 11. Product lifecycle

```text
DISCOVERED
    ↓
FILTERED
    ↓
RESEARCHING
    ↓
VALIDATED
    ↓
READY_FOR_TEST
    ↓
TESTING
    ↓
WINNER
    ↓
SCALING
```

Estados alternativos:

```text
REJECTED
PAUSED
EXHAUSTED
```

---

## 12. Data ownership

La base de datos debe diferenciar:

- datos originales;
- datos calculados;
- datos estimados;
- datos generados por IA.

Siempre que sea posible, conservar:

- fuente;
- fecha;
- versión;
- confidence;
- método utilizado.

---

## 13. Analytics loop

```text
PRODUCT
  ↓
CAMPAIGN
  ↓
ORDER
  ↓
DELIVERY RESULT
  ↓
PROFIT
  ↓
HISTORICAL DATA
  ↓
SCORING IMPROVEMENT
```

La ventaja competitiva del sistema debe surgir de los datos históricos acumulados.

---

## 14. Orchestrator

El orchestrator coordina, pero no implementa toda la lógica.

Ejemplo:

```text
discover product
→ product analysis
→ market research
→ economics
→ scoring
→ creative
→ landing
→ ads
→ customer
→ order
→ analytics
```

El orchestrator no debe duplicar lógica que pertenece a otras capas.

---

## 15. Error handling

Las integraciones externas deben manejar:

- timeout;
- rate limits;
- autenticación;
- cambios de HTML;
- respuestas incompletas;
- datos faltantes;
- errores temporales.

La lógica de negocio no debe romperse por detalles de un proveedor externo.

---

## 16. Observability

Registrar al menos:

- ejecución;
- proveedor;
- operación;
- duración;
- resultado;
- error;
- product_id;
- correlation_id cuando exista.

Nunca registrar secretos.

---

## 17. Migración

No realizar una migración completa de arquitectura en una sola tarea.

Orden recomendado:

1. identificar límites actuales;
2. extraer interfaces;
3. mover lógica gradualmente;
4. mantener tests verdes;
5. eliminar duplicación;
6. continuar con el siguiente módulo.
