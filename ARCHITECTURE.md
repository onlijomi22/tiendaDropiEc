# Architecture Guide - TiendaDropiEc

## Overview

TiendaDropiEc uses **Clean Architecture** with **SOLID principles** and **Spec Driven Development (SDD)**.

## Layer Dependency Rules

```
domain/ ← (no external dependencies)
    ↑
application/ ← depends on domain interfaces only
    ↑
agents/ ← depends on application use cases
    ↑
infrastructure/ → implements domain interfaces
    ↑
scripts/ → wires everything together (entry points)
```

**Rule**: Inner layers NEVER import from outer layers.

## SDD Workflow

1. Write/update spec in `specs/<domain>/<entity>.spec.md`
2. Update `.feature` file in `tests/features/<domain>/`
3. Implement domain entity deriving rules from spec
4. Write use case in `application/<domain>/`
5. Run tests: `pytest tests/`
6. Implement infrastructure concrete class

## Adding a New Domain

1. Create `specs/<domain>/<entity>.spec.md`
2. Create `tests/features/<domain>/<scenario>.feature`
3. Create `src/domain/<domain>/entities.py` (Pydantic models)
4. Create `src/domain/<domain>/repositories.py` (ABC interface)
5. Create `src/application/<domain>/` (use cases)
6. Create `src/infrastructure/<domain>/` (concrete impl)
7. Create `src/agents/<domain>_agent.py`
8. Add to `OrchestratorAgent.agent_tools`

## Running the System

```bash
# Install dependencies
poetry install
playwright install chromium

# Copy and fill credentials
cp .env.example .env

# Run manually (one-shot)
python scripts/run_orchestrator.py

# Run with custom task
python scripts/run_orchestrator.py --task "Analiza categoría belleza"

# Run automatically (scheduled)
python scripts/scheduler.py

# Run tests
pytest tests/
pytest tests/unit/  # Unit tests only
pytest tests/step_defs/  # BDD tests only
```

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Playwright for Dropi | No official Dropi API - PageObjectModel makes scraping maintainable |
| Pydantic v2 entities | Living spec enforcement - invalid data raises at construction time |
| SpecViolationError | Explicitly links runtime errors to spec criteria (e.g., CA-PROD-02) |
| Skills not Supabase | Zero-config knowledge base, easily editable, migrateable later |
| APScheduler | Lightweight cron - no external queue needed for current scale |
| BaseAgent ReAct | Composable pattern - each agent is independent and testable |
