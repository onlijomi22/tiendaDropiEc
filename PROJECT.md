# TiendaDropiEc

## 1. Visión del proyecto

TiendaDropiEc es una plataforma de **AI Commerce para Ecuador**, diseñada para automatizar y mejorar el ciclo completo de venta de productos de dropshipping.

El proveedor inicial es **Dropi**, pero la arquitectura debe permitir integrar otros proveedores en el futuro sin rehacer la lógica central del sistema.

La meta no es simplemente crear tiendas o publicar productos. La plataforma debe convertirse en un sistema capaz de:

- descubrir productos;
- analizar rentabilidad;
- analizar competencia y demanda;
- detectar tendencias;
- seleccionar productos con mayor probabilidad de éxito;
- generar landing pages;
- generar creativos y anuncios;
- automatizar atención y ventas por WhatsApp;
- crear y hacer seguimiento de pedidos;
- medir resultados reales;
- utilizar los resultados para mejorar decisiones futuras.

---

## 2. Mercado inicial

- País inicial: Ecuador
- Expansión futura: Latinoamérica
- Modelo inicial: dropshipping
- Proveedor inicial: Dropi
- Canal comercial prioritario: redes sociales + landing page + WhatsApp

---

## 3. Principio central

El objetivo del sistema NO es maximizar ventas brutas.

El objetivo es maximizar:

> **EXPECTED PROFIT PER DELIVERED ORDER**

Cada decisión relacionada con productos, publicidad y escalamiento debe considerar rentabilidad real y no únicamente ingresos, clics o cantidad de pedidos.

---

## 4. Flujo principal

```text
PRODUCT DISCOVERY
        ↓
PRODUCT FILTERING
        ↓
MARKET RESEARCH
        ↓
ECONOMICS ANALYSIS
        ↓
PRODUCT SCORING
        ↓
CREATIVE INTELLIGENCE
        ↓
LANDING PAGE
        ↓
ADS
        ↓
WHATSAPP / CUSTOMER
        ↓
ORDER
        ↓
DELIVERY
        ↓
ANALYTICS
        ↓
LEARNING
```

---

## 5. Capacidades principales

### Product Intelligence

Debe analizar:

- costo del producto;
- precio sugerido;
- stock;
- proveedor;
- rating del proveedor;
- calidad de fotografías;
- categoría;
- características;
- potencial de demostración;
- dificultad de encontrarlo localmente.

### Market Intelligence

Debe analizar:

- competencia;
- precios de mercado;
- Google Trends;
- tendencias sociales;
- marketplaces;
- saturación;
- demanda;
- temporalidad;
- señales de interés.

### Economics

Debe calcular como mínimo:

- margen bruto;
- margen de contribución;
- CPA máximo;
- break-even CPA;
- utilidad estimada;
- utilidad esperada;
- impacto de devoluciones;
- impacto de pedidos rechazados;
- impacto de cancelaciones.

### Creative Intelligence

Debe generar o identificar:

- buyer persona;
- problema principal;
- propuesta de valor;
- ángulos de venta;
- hooks;
- guiones;
- CTA;
- estructuras de video;
- variantes de anuncios.

### Landing Pages

Debe poder crear landing pages orientadas a conversión utilizando información real del producto.

### Customer / WhatsApp

Debe:

- responder preguntas;
- resolver objeciones;
- recomendar productos;
- capturar datos;
- confirmar pedidos;
- hacer seguimiento.

Nunca debe inventar:

- stock;
- precios;
- descuentos;
- tiempos de entrega;
- políticas;
- características del producto.

### Orders

Debe controlar:

- creación;
- confirmación;
- cancelación;
- despacho;
- tracking;
- entrega;
- rechazo;
- devolución.

### Analytics

Debe medir como mínimo:

- CTR;
- CPC;
- CPA;
- tasa de conversión;
- tasa de confirmación;
- tasa de entrega;
- tasa de rechazo;
- tasa de devolución;
- ROAS;
- utilidad neta;
- utilidad por pedido entregado.

---

## 6. Estados de un producto

```text
DISCOVERED
FILTERED
RESEARCHING
VALIDATED
READY_FOR_TEST
TESTING
WINNER
SCALING
PAUSED
REJECTED
EXHAUSTED
```

Los cambios de estado deben depender de reglas y datos explícitos.

---

## 7. Principios de arquitectura

1. Dropi es un proveedor, no el dominio principal.
2. Las integraciones externas deben utilizar adapters.
3. La lógica de negocio no debe depender directamente de APIs externas.
4. Ningún LLM debe ser tratado como fuente factual.
5. Los datos reales deben tener prioridad sobre las inferencias de IA.
6. Las reglas de negocio configurables no deben estar hardcodeadas.
7. Las decisiones importantes deben poder auditarse.
8. Los módulos deben tener responsabilidades claras.
9. Las modificaciones importantes deben incluir tests.
10. Se debe evitar duplicar lógica entre skills y código.

---

## 8. IA y modelos

La arquitectura debe permitir intercambiar proveedores de IA.

Posibles proveedores:

- Claude
- OpenAI
- Gemini
- modelos locales

La lógica del dominio no debe depender de un proveedor específico.

---

## 9. NotebookLM / conocimiento externo

NotebookLM puede utilizarse como fuente de investigación y síntesis para:

- videos;
- cursos;
- casos de estudio;
- transcripciones;
- anuncios;
- patrones creativos;
- estructuras de ofertas.

NotebookLM NO debe ser una dependencia central del sistema.

---

## 10. Criterio de éxito del MVP

El MVP se considera útil cuando puede:

1. obtener productos;
2. descartar productos inviables;
3. analizar economía;
4. investigar mercado;
5. asignar un score;
6. seleccionar productos para prueba;
7. generar una landing;
8. generar propuestas de anuncios;
9. registrar resultados;
10. utilizar los resultados para mejorar decisiones futuras.
