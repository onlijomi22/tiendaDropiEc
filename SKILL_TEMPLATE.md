# Skill: <NAME>

## Purpose

Describe una sola responsabilidad principal.

---

## Inputs

- input_1
- input_2

---

## Outputs

- output_1
- output_2

---

## Workflow

1. Paso 1
2. Paso 2
3. Paso 3

---

## Rules

- Regla 1
- Regla 2

---

## Data Sources

- Fuente 1
- Fuente 2

---

## Tools

- Tool 1
- Tool 2

---

## Must Not

- No inventar datos.
- No asumir valores ausentes.
- No modificar módulos fuera del alcance.
- No duplicar responsabilidades de otras skills.

---

## Failure Conditions

La skill debe detenerse o devolver estado de error cuando:

- falten datos obligatorios;
- la fuente no sea accesible;
- los datos sean contradictorios;
- el resultado no tenga suficiente evidencia.

---

## Output Contract

```json
{
  "status": "SUCCESS",
  "data": {},
  "warnings": [],
  "sources": []
}
```

---

## Tests

- Caso normal
- Datos faltantes
- Fuente no disponible
- Valores extremos
- Respuesta inválida

---

## Examples

Agregar ejemplos reales cuando existan.
