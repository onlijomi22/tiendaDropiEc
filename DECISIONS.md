# Architecture Decisions

Este archivo registra decisiones importantes del proyecto para evitar que futuras sesiones de desarrollo contradigan decisiones anteriores.

---

## ADR-001 — Dropi no pertenece al dominio

**Estado:** Aceptado

Dropi debe tratarse como una integración externa.

La lógica central debe poder funcionar con otros proveedores.

---

## ADR-002 — Configuración fuera de la lógica de negocio

**Estado:** Aceptado

Umbrales como:

- precio mínimo;
- margen mínimo;
- stock mínimo;
- rating mínimo;
- pesos del scoring;

no deben quedar hardcodeados en múltiples lugares.

Deben centralizarse en configuración.

---

## ADR-003 — Rentabilidad antes de creatividad

**Estado:** Aceptado

No invertir recursos significativos en generar:

- videos;
- anuncios;
- landing pages;

para productos que no hayan superado primero un análisis económico mínimo.

---

## ADR-004 — El LLM no es una fuente factual

**Estado:** Aceptado

Claude, OpenAI, Gemini, NotebookLM u otros modelos pueden:

- analizar;
- resumir;
- clasificar;
- proponer;
- generar.

No deben utilizarse como fuente única para afirmar:

- precio;
- stock;
- demanda;
- ventas;
- tendencias;
- CPA;
- ROAS.

---

## ADR-005 — Trazabilidad de datos

**Estado:** Aceptado

Siempre que sea posible, conservar:

- fuente;
- fecha;
- tipo de dato;
- origen;
- cálculo;
- versión.

---

## ADR-006 — Scoring configurable

**Estado:** Aceptado

El Product Score debe poder ajustarse sin modificar código.

El objetivo futuro es calibrar los pesos con resultados reales.

---

## ADR-007 — Skills pequeñas y especializadas

**Estado:** Aceptado

Evitar skills monolíticas.

Cada skill debe tener:

- propósito;
- entradas;
- salidas;
- reglas;
- límites;
- failure conditions.

---

## ADR-008 — Tests como requisito

**Estado:** Aceptado

La lógica importante debe estar cubierta por tests.

No se considera completa una modificación si rompe tests existentes.

---

## ADR-009 — Arquitectura incremental

**Estado:** Aceptado

No rehacer el proyecto completo para alcanzar una arquitectura ideal.

Migrar gradualmente manteniendo funcionalidad.

---

## ADR-010 — Métrica principal

**Estado:** Aceptado

La métrica económica principal del sistema será:

> Expected Profit Per Delivered Order

Ventas brutas y ROAS son métricas útiles, pero no suficientes por sí mismas.

---

## ADR-011 — NotebookLM como fuente auxiliar

**Estado:** Aceptado

NotebookLM puede aportar conocimiento, patrones y síntesis.

No será una dependencia central del sistema.

---

## ADR-012 — Integraciones reemplazables

**Estado:** Aceptado

El proyecto debe permitir reemplazar progresivamente:

- proveedor de productos;
- proveedor LLM;
- canal de mensajería;
- canal publicitario;
- fuente de tendencias.
