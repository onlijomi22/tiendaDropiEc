# Spec Driven Development — TiendaDropiEc

## ¿Qué es SDD en este proyecto?

Spec Driven Development significa que **las especificaciones son la fuente de verdad**.
El código existe para satisfacer las specs, no al revés.

## Flujo de trabajo SDD

```
1. SPEC (.spec.md) → Define QUÉ debe hacer el sistema
       ↓
2. FEATURE (.feature) → Define comportamientos en lenguaje Gherkin (BDD)
       ↓
3. ENTITIES (entities.py) → Pydantic models derivados de la spec
       ↓
4. INTERFACES (repositories.py) → ABCs derivadas de la spec
       ↓
5. USE CASES (application/) → Implementan la spec
       ↓
6. TESTS (step_defs/) → Validan que el código cumple la spec
       ↓
7. INFRA (infrastructure/) → Implementación concreta
```

## Estructura de Specs

```
specs/
├── README.md              ← Este archivo
├── products/
│   └── product.spec.md    ← Spec del dominio productos
├── ads/
│   └── campaign.spec.md   ← Spec del dominio campañas
├── customer/
│   └── conversation.spec.md
└── analytics/
    └── report.spec.md
```

## Reglas

1. **No code sin spec**: Antes de crear cualquier módulo, existe su `.spec.md`
2. **Specs son inmutables en sprint**: No se cambia una spec durante un sprint activo
3. **Tests derivan de specs**: Cada criterio de aceptación en la spec → un test
4. **Gherkin es el contrato**: Los `.feature` files son contratos entre dominio y agentes
