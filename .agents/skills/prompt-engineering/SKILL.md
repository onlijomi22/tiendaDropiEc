---
name: prompt-engineering
description: Principios avanzados de Ingeniería de Prompts (Estructura, Tono y Contexto) aplicados a los agentes de e-commerce y dropshipping.
---

# Skill: Ingeniería de Prompts para E-commerce

## Contexto y Estructura Base

Basado en la metodología estructurada de ingeniería de prompts, cada interacción con los LLMs (como Gemini) dentro de nuestro sistema de agentes debe diseñarse bajo un marco estricto que evite alucinaciones y maximice la conversión de ventas.

Un prompt bien estructurado consta de **5 componentes esenciales**:

```
[ROL / PERSONA] → [CONTEXTO DE NEGOCIO] → [TAREA ESPECÍFICA] → [TONO Y ESTILO] → [FORMATO DE SALIDA]
```

---

## 1. El Rol (Persona)
Define la identidad y el nivel de experiencia del modelo.
*   **Mal Rol:** "Eres un escritor."
*   **Buen Rol (E-commerce):** "Actúas como un Copywriter experto en Dropshipping y Comercio Electrónico de Conversión Directa para el mercado de Ecuador, con más de 8 años redactando anuncios de alto impacto en TikTok Ads y Meta Ads."

## 2. El Contexto
Establece la situación, limitaciones y por qué se hace la tarea.
*   **Contexto de Negocio:** El producto se entrega mediante **Pago Contra Entrega (Cash on Delivery)**, lo cual elimina el miedo a la estafa online en Ecuador. El envío se hace en 24-48 horas. La audiencia proviene principalmente de tráfico frío impulsivo en TikTok.

## 3. La Tarea
Instrucción directa y sin rodeos utilizando verbos de acción.
*   **Especificidad:** Redactar 3 versiones de copy para anuncios de Meta, un gancho de 3 segundos para TikTok y la estructura de objeciones para la landing page.
*   **Restricciones de Datos:** No asumas características del producto que no estén en la descripción cruda. Usa la información real de MercadoLibre para fijar la ventaja de precio.

## 4. El Tono
Define cómo se siente la marca al leerse.
*   **Enfoque Conversacional / Persuasivo:** El tono debe ser entusiasta, directo, urgente pero confiable. 
*   **Reglas de Tono en Dropshipping:**
    *   *Evitar:* Lenguaje excesivamente formal o técnico que abrume al cliente.
    *   *Fomentar:* Palabras que alivien dolores (Ej. "Fácil", "Sin esfuerzo", "En casa", "Paga al recibir").

## 5. El Formato
El tipo de estructura de la respuesta.
*   **Definición:** JSON con claves específicas (`headline`, `body`, `tiktok_script`) para que el backend de Python lo procese de forma segura sin texto basura alrededor.

---

## Aplicación Práctica en TiendaDropiEc

### Prompt Template para Redacción de Copy de Landing Pages (Basado en Fórmulas E-commerce)
Para generar conversiones altas, como recomienda Shopify, usamos frameworks comprobados de copywriting dentro del prompt. Este formato se mapea directamente en nuestro `EnrichProductUseCase`.

**Fórmulas soportadas que puedes pedirle a Gemini que use:**
1. **PAS (Problema, Agitación, Solución):** Ideal para productos que resuelven un dolor fuerte.
2. **AIDA (Atención, Interés, Deseo, Acción):** Ideal para productos novedosos o "Wow factor".
3. **FAB (Características, Ventajas, Beneficios):** Ideal para productos técnicos o electrónicos.

**Ejemplo de Prompt Maestro:**
```text
Eres un Copywriter experto en Landing Pages de comercio electrónico de alta conversión.
Tu cliente vende en Ecuador mediante pago contra entrega.

CONTEXTO DEL PRODUCTO:
- Nombre: {product_name}
- Detalles: {product_description}
- Dolores encontrados en el mercado ecuatoriano: {customer_concerns}
- Ventajas valoradas: {customer_positives}

TAREA:
Redacta el borrador de venta de la landing page utilizando la fórmula de copywriting PAS (Problema, Agitación, Solución). 

REGLAS DE TONO:
- Sé directo y empático.
- Enfócate en erradicar los dolores y resaltar los beneficios de forma pragmática.
- Usa lenguaje emocional pero creíble, como recomiendan las mejores prácticas de Shopify.

FORMATO DE SALIDA (JSON estrictamente estructurado):
- "landing_headline": Título persuasivo (La Atención/Problema).
- "landing_subheadline": Subtítulo que resalte la entrega gratis y pago al recibir.
- "benefits": Lista de 3 viñetas (La Solución/Beneficios).
- "objection_handlers": Respuesta a 2 miedos reales de los compradores.
```

---

## Metodología de Optimización Continua (Iteración)

1.  **Grounded Knowledge First:** Nunca le pidas a la IA escribir sobre un producto sin inyectarle primero la información del scraper de MercadoLibre y la búsqueda en Google.
2.  **Few-Shot Examples (Opcional):** Si quieres cambiar el estilo de un copy, agrega un ejemplo de un anuncio exitoso anterior al prompt de redacción.
3.  **Evaluación de Salida:** Los resultados se validan contra los límites de caracteres del Dominio de Ads antes de guardarse.
