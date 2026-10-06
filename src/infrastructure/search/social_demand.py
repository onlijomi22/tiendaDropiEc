"""Social demand signals via Gemini grounded search.

Queries real social platforms (Facebook, TikTok, forums) to assess
whether people are actively buying/discussing a product in Ecuador.
"""

from __future__ import annotations

from src.infrastructure.ai.gemini_adapter import GeminiAdapter
from src.shared.logger import logger


class SocialDemandSearch:
    """Assess social demand for a product using Gemini web search."""

    def __init__(self, gemini_adapter: GeminiAdapter | None = None) -> None:
        self._gemini = gemini_adapter or GeminiAdapter(model="gemini-3.6-flash")

    async def assess_demand(self, product_name: str, category: str = "", country: str = "Ecuador") -> dict:
        """Search social platforms for demand signals.

        Args:
            product_name: Product to research.
            category: Product category.
            country: Target market.

        Returns:
            Dict with social_score (0.0-1.0), signals found, competition level.
        """
        prompt = f"""Busca en internet informacion REAL sobre la demanda del producto "{product_name}"
(categoria: {category}) en {country}.

Investiga especificamente:
1. Se vende en Facebook Marketplace {country}? Cuantos vendedores hay aproximadamente?
2. Hay videos de TikTok mostrando o vendiendo este producto en {country} o Latinoamerica?
3. Se vende en MercadoLibre {country}? A que precio promedio?
4. Hay grupos de Facebook donde lo vendan o lo pidan?

Responde en JSON:
{{
    "facebook_marketplace_sellers": 0,
    "facebook_marketplace_price_range": "$X - $Y o desconocido",
    "tiktok_videos_found": false,
    "tiktok_engagement": "alto/medio/bajo/ninguno",
    "mercadolibre_listings": 0,
    "mercadolibre_avg_price": 0,
    "facebook_groups_activity": "alta/media/baja/ninguna",
    "overall_demand": "alta/media/baja/muy_baja",
    "social_score": 0.5,
    "demand_summary": "resumen en 1 oracion",
    "recommendation": "vender/investigar_mas/evitar"
}}

social_score: 0.0=nadie lo busca, 0.5=demanda moderada, 1.0=alta demanda viral.
Basa tu respuesta SOLO en lo que encuentres. No inventes datos."""

        try:
            logger.info(f"[SocialDemand] Researching: {product_name} in {country}")
            data = await self._gemini.generate_json_with_search(prompt)
            if data:
                score = data.get("social_score", 0.5)
                # Clamp to valid range
                data["social_score"] = max(0.0, min(1.0, float(score)))
                logger.info(
                    f"[SocialDemand] {product_name}: score={data['social_score']}, "
                    f"demand={data.get('overall_demand', '?')}"
                )
                return data
            return self._fallback()
        except Exception as e:
            logger.warning(f"[SocialDemand] Failed: {e}")
            return self._fallback()

    def _fallback(self) -> dict:
        return {
            "social_score": 0.5,
            "overall_demand": "desconocida",
            "demand_summary": "No se pudo evaluar demanda social",
            "recommendation": "investigar_mas",
        }
