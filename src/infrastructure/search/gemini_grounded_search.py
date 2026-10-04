"""Gemini with Google Search Grounding for real market research.

Uses Gemini's built-in Google Search tool to retrieve real web data
before generating insights. This eliminates hallucination because
Gemini reads actual pages before responding.

Spec: specs/intelligence/product_intelligence.spec.md#CA-INTEL-01
"""

from __future__ import annotations
from src.infrastructure.ai.gemini_adapter import GeminiAdapter
from src.shared.logger import logger


class GeminiGroundedSearch:
    """Wrapper for Gemini API with Google Search grounding enabled.

    When search grounding is active, Gemini:
    1. Receives the prompt
    2. Searches Google for relevant results
    3. Reads the actual pages
    4. Generates a response citing real sources

    This gives us real market data without hallucination.
    """

    def __init__(self, gemini_adapter: GeminiAdapter | None = None) -> None:
        self._gemini = gemini_adapter or GeminiAdapter(model="gemini-3.6-flash")

    async def research_product_category(
        self,
        product_name: str,
        category: str,
        country: str = "Ecuador",
    ) -> dict:
        """Research buyer behavior for a product category using real web data.

        Args:
            product_name: Product to research (e.g., 'licuadora portatil').
            category: Product category (e.g., 'cocina', 'hogar').
            country: Target market country.

        Returns:
            Dict with buyer_concerns, buyer_positives, and sources.
        """
        prompt = f"""Investiga el mercado de "{product_name}" (categoria: {category})
        para compradores en {country} que compran por internet.

        Busca informacion REAL sobre:
        1. Cuales son las principales preocupaciones de los compradores ANTES de comprar este tipo de producto?
        2. Que es lo que mas valoran los compradores DESPUES de comprarlo?
        3. Extrae de 2 a 3 RESENAS REALES o comentarios literales de compradores (buscalas en foros, ML, redes).

        Responde en este formato JSON exacto:
        {{
            "buyer_concerns": ["preocupacion 1", "preocupacion 2", "preocupacion 3"],
            "buyer_positives": ["positivo 1", "positivo 2", "positivo 3"],
            "real_reviews": ["resena textual 1", "resena textual 2"],
            "market_summary": "resumen del mercado en 2 oraciones",
            "sources_used": ["descripcion de fuentes consultadas"]
        }}

        Basa tu respuesta SOLO en lo que encontraste en la web.
        Si no encuentras datos suficientes, indicalo en market_summary.
        No inventes datos."""

        try:
            logger.info(f"[GeminiSearch] Researching: {product_name} in {country}")
            data = await self._gemini.generate_json_with_search(prompt)
            if data:
                logger.info(
                    f"[GeminiSearch] Found {len(data.get('buyer_concerns', []))} concerns, "
                    f"{len(data.get('buyer_positives', []))} positives"
                )
                return data
            logger.warning("[GeminiSearch] Could not parse JSON from response")
            return self._fallback_response(product_name)
        except Exception as e:
            logger.error(f"[GeminiSearch] Error: {e}")
            return self._fallback_response(product_name)

    def _fallback_response(self, product_name: str) -> dict:
        """Return empty structure when search fails."""
        return {
            "buyer_concerns": [],
            "buyer_positives": [],
            "objections": [],
            "market_summary": f"No se encontraron datos suficientes para '{product_name}'",
            "sources_used": []
        }
