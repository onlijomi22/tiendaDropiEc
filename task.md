# TiendaDropiEc — Task List

## Fase 0 — Fundación (COMPLETADO ✅)
- [x] pyproject.toml + .env.example
- [x] specs/ — SDD fuente de verdad (products, ads, customer, analytics)
- [x] src/shared/ — config, logger, gemini_client, exceptions
- [x] src/domain/ — entities + repositories (4 dominios)
- [x] src/application/ — use cases (analyze_product, find_winners, generate_copy, handle_message, generate_report)
- [x] src/agents/base_agent.py — ReAct loop
- [x] src/infrastructure/dropi/ — browser, scraper, product_repo
- [x] src/infrastructure/whatsapp/ — client
- [x] src/agents/ — product_analyst, orchestrator
- [x] tests/ — 17 tests BDD + unit pasando
- [x] .agents/skills/ — 4 skills (products, ads, customer, analytics)
- [x] ARCHITECTURE.md

## Fase 1 — Product Intelligence (EN PROGRESO 🔄)
- [x] specs/intelligence/product_intelligence.spec.md
- [x] src/domain/intelligence/entities.py
- [x] src/infrastructure/search/gemini_grounded_search.py
- [x] src/infrastructure/search/mercadolibre_scraper.py
- [x] src/application/intelligence/enrich_product.py
- [x] scripts/analyze_product.py
- [ ] Configurar .env con GEMINI_API_KEY real
- [ ] Calibrar selectores MercadoLibre Ecuador (validar con producto real)
- [ ] Calibrar Playwright login Dropi (validar con credenciales reales)
- [ ] Seleccionar 3 productos piloto y correr analyze_product.py

## Fase 2 — Frontend Next.js (PENDIENTE)
- [ ] Inicializar Next.js en frontend/
- [ ] Componente LandingHero, CTAForm, WhatsAppButton
- [ ] Ruta dinámica /[categoria]/[producto]
- [ ] FastAPI en Contabo exponiendo datos de productos
- [ ] Deploy en Vercel

## Fase 3 — Creativos IA (PENDIENTE)
- [ ] CreativesAgent: imagen Meta Ads (Gemini Imagen)
- [ ] CreativesAgent: guión TikTok
- [ ] Integrar con landing page

## Fase 4 — Ads + WhatsApp (PENDIENTE)
- [ ] AdsManagerAgent implementado (Google Ads + TikTok Ads real)
- [ ] WhatsApp webhook receiver
- [ ] CustomerSupportAgent con contexto de conversación

## Fase 5 — Orders + Analytics (PENDIENTE)
- [ ] OrdersAgent: crear pedido en Dropi vía Playwright
- [ ] OrdersAgent: tracking y notificación por WhatsApp
- [ ] AnalyticsAgent con datos reales de Dropi Wallet
- [ ] Loop de optimización
