# Claude Development Instructions

## 1. Objetivo

Trabaja sobre este repositorio como desarrollador senior y revisor de arquitectura.

Antes de realizar cambios debes comprender el contexto del proyecto.

---

## 2. Lectura inicial obligatoria

Antes de modificar código:

1. Leer `PROJECT.md`.
2. Leer `ARCHITECTURE.md`.
3. Leer `DECISIONS.md` si existe.
4. Leer el `SKILL.md` asociado a la funcionalidad solicitada.
5. Inspeccionar la implementación existente.
6. Inspeccionar los tests existentes.

No modificar código antes de comprender la implementación actual.

---

## 3. Alcance

No modificar módulos que no estén relacionados con la tarea actual.

Si una tarea afecta únicamente productos, no modificar:

- frontend no relacionado;
- anuncios;
- WhatsApp;
- pedidos;
- analytics;

salvo que exista una dependencia real y se explique antes.

---

## 4. Antes de implementar

Para cambios significativos:

1. Explicar brevemente el problema.
2. Identificar archivos afectados.
3. Proponer la solución.
4. Detectar riesgos.
5. Implementar únicamente después del análisis.

No hacer refactors masivos innecesarios.

---

## 5. Reglas de código

- Respetar patrones existentes.
- Evitar duplicación de lógica.
- Mantener funciones pequeñas y enfocadas.
- Usar nombres claros.
- Preferir modelos tipados cuando existan.
- Mantener configuración fuera de la lógica de negocio.
- No incluir credenciales en código.
- Utilizar variables de entorno para secretos.
- Mantener integraciones externas detrás de interfaces/adapters.

---

## 6. Integraciones externas

El dominio no debe depender directamente de:

- Dropi;
- Meta;
- TikTok;
- WhatsApp;
- Claude;
- OpenAI;
- Gemini;
- NotebookLM;
- Google Trends.

Utilizar interfaces y adapters cuando sea razonable.

Ejemplo conceptual:

```text
Domain
  ↓
Application Service
  ↓
Interface
  ↓
Adapter
  ↓
External Provider
```

---

## 7. Datos

Nunca inventar datos.

No inferir como hechos:

- stock;
- precios;
- costos;
- rating;
- tendencias;
- competencia;
- CPA;
- ROAS;
- conversión;
- ventas;
- utilidad;
- tiempos de entrega.

Cuando un dato no esté disponible, utilizar un estado como:

```text
UNKNOWN
NOT_AVAILABLE
PENDING_RESEARCH
```

---

## 8. IA

Una respuesta de un LLM no es una fuente factual.

Separar claramente:

- datos observados;
- datos calculados;
- hipótesis;
- estimaciones;
- contenido generado por IA.

Toda estimación debe ser identificable.

---

## 9. Tests

Una tarea no se considera terminada hasta que:

1. se ejecutan los tests relevantes;
2. se revisan regresiones;
3. se informan tests fallidos;
4. no se oculten errores;
5. no se eliminen tests para hacer pasar la suite.

Cuando se agregue lógica de negocio importante, agregar tests.

---

## 10. Cambios

Al finalizar una tarea, informar:

- archivos modificados;
- funcionalidad implementada;
- decisiones tomadas;
- tests ejecutados;
- tests fallidos;
- riesgos pendientes;
- deuda técnica detectada.

---

## 11. Git

No hacer commits salvo que el usuario lo solicite.

Antes de cambios grandes, recomendar trabajar con un árbol Git limpio.

No eliminar cambios existentes del usuario.

---

## 12. Skills

Cada skill debe tener una responsabilidad específica.

Evitar una skill que haga simultáneamente:

- scraping;
- análisis económico;
- investigación de mercado;
- creación de anuncios;
- creación de pedidos.

Cuando una skill crezca demasiado, proponer separación de responsabilidades.

---

## 13. Restricciones de seguridad

Nunca:

- exponer secretos;
- imprimir tokens privados;
- guardar passwords;
- subir `.env`;
- modificar archivos de credenciales sin autorización;
- ejecutar operaciones destructivas sin avisar.

---

## 14. Uso eficiente de contexto

No leer todo el repositorio si no es necesario.

Preferir:

1. documentos de contexto;
2. skill relevante;
3. módulo relevante;
4. tests relevantes.

Abrir logs, capturas, HTML de debug o grandes archivos de datos únicamente cuando sean necesarios para la tarea.

---

## 15. Filosofía de trabajo

Preferir:

```text
analizar
→ proponer
→ implementar
→ probar
→ resumir
```

Evitar:

```text
asumir
→ modificar muchos archivos
→ esperar que funcione
```
