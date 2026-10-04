"""Use case: Analyze a competitor's landing page.

Uses MarkItDown to fetch page content and Gemini to analyze strategy.
"""

import logging
from pydantic import BaseModel, Field
from src.infrastructure.ai.gemini_adapter import GeminiAdapter
from src.infrastructure.parsers.markitdown_parser import MarkItDownParser

logger = logging.getLogger(__name__)


class CompetitorAnalysisResult(BaseModel):
    url: str
    headline_found: str = Field(description="El titulo o hook principal usado en la pagina.")
    price_found_usd: float = Field(description="El precio de venta detectado, en dolares.")
    pain_points_addressed: list[str] = Field(description="Lista de dolores/problemas del cliente que la pagina intenta resolver.")
    benefits_highlighted: list[str] = Field(description="Los beneficios principales que destacan.")
    improvement_recommendations: list[str] = Field(description="Recomendaciones para superar a este competidor en nuestra propia landing.")


class AnalyzeCompetitorUseCase:
    """Uses MarkItDown to fetch a competitor's page and Gemini to analyze their strategy."""

    def __init__(self, gemini_adapter: GeminiAdapter | None = None):
        self._md_parser = MarkItDownParser()
        self._gemini = gemini_adapter or GeminiAdapter()

    async def execute(self, url: str) -> CompetitorAnalysisResult:
        logger.info(f"[AnalyzeCompetitor] Initiating analysis for URL: {url}")

        # 1. Fetch and clean content to Markdown
        markdown_content = await self._md_parser.convert_url(url)

        if len(markdown_content) > 100000:
            logger.warning("[AnalyzeCompetitor] Content very long, truncating to 100k chars.")
            markdown_content = markdown_content[:100000]

        # 2. Analyze with Gemini
        prompt = f"""
Actuas como un experto Analista de Inteligencia Competitiva para E-Commerce.
He utilizado una herramienta (MarkItDown) para extraer el contenido en Markdown de la Landing Page / Tienda de un competidor.

URL del competidor: {url}

CONTENIDO DE LA PAGINA:
---
{markdown_content}
---

TAREA:
Analiza el copy, la estructura y la oferta de esta pagina.
Devuelve un JSON estrictamente estructurado (sin codigo markdown extra alrededor) con el siguiente formato:

{{
    "headline_found": "El gancho principal o titular de la pagina",
    "price_found_usd": 15.99,
    "pain_points_addressed": ["dolor 1", "dolor 2"],
    "benefits_highlighted": ["beneficio 1", "beneficio 2"],
    "improvement_recommendations": [
        "Que podriamos hacer mejor nosotros en nuestra pagina",
        "Oportunidades de copy que ellos ignoraron"
    ]
}}
"""
        try:
            logger.info("[AnalyzeCompetitor] Sending Markdown to Gemini for analysis...")
            data = await self._gemini.generate_json(prompt)

            return CompetitorAnalysisResult(
                url=url,
                headline_found=data.get("headline_found", "No detectado"),
                price_found_usd=float(data.get("price_found_usd", 0.0)),
                pain_points_addressed=data.get("pain_points_addressed", []),
                benefits_highlighted=data.get("benefits_highlighted", []),
                improvement_recommendations=data.get("improvement_recommendations", [])
            )
        except Exception as e:
            logger.error(f"[AnalyzeCompetitor] Gemini Analysis failed: {e}")
            raise
