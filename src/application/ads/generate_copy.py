"""Use case: Generate ad copy for a product using Gemini AI.

Spec: specs/ads/campaign.spec.md
Criteria: CA-ADS-01 (character limits enforced by AdCopy entity)
"""

from dataclasses import dataclass
from src.domain.ads.entities import AdCopy, AdPlatform
from src.domain.products.entities import Product
from src.infrastructure.ai.gemini_adapter import GeminiAdapter
from src.shared.logger import logger


@dataclass
class GenerateCopyInput:
    """Input DTO for ad copy generation."""
    product: Product
    platform: AdPlatform


class GenerateCopyUseCase:
    """Generate platform-specific ad copy using Gemini AI.

    Character limits are enforced by the AdCopy domain entity (CA-ADS-01).
    This use case only handles prompt engineering and Gemini calls.
    """

    def __init__(self, gemini_adapter: GeminiAdapter | None = None) -> None:
        self._gemini = gemini_adapter or GeminiAdapter()

    async def execute(self, input_data: GenerateCopyInput) -> AdCopy:
        """Generate ad copy for a product.

        Args:
            input_data: Product and target platform.

        Returns:
            AdCopy validated against platform character limits.

        Raises:
            SpecViolationError: If generated copy exceeds character limits.
        """
        prompt = self._build_prompt(input_data)
        logger.info(f"Generating {input_data.platform} copy for: {input_data.product.name}")

        text = await self._gemini.generate(prompt)
        return self._parse_response(text, input_data.platform)

    def _build_prompt(self, input_data: GenerateCopyInput) -> str:
        """Build a Gemini prompt for ad copy generation."""
        p = input_data.product
        limits = (
            "Headline: maximo 30 caracteres. Description: maximo 90 caracteres."
            if input_data.platform == AdPlatform.GOOGLE
            else "Headline: maximo 100 caracteres."
        )
        return (
            f"Eres un experto en copywriting de dropshipping para mercado latinoamericano.\n"
            f"Genera copy publicitario para {input_data.platform.value} Ads en ESPANOL.\n"
            f"Producto: {p.name}\n"
            f"Descripcion: {p.description[:200]}\n"
            f"Precio de venta: ${p.suggested_price:.2f} USD\n"
            f"Restricciones: {limits}\n\n"
            f"Responde EXACTAMENTE en este formato (sin explicaciones adicionales):\n"
            f"HEADLINE: [texto]\n"
            f"DESCRIPTION: [texto]\n"
            f"CTA: [texto corto]"
        )

    def _parse_response(self, text: str, platform: AdPlatform) -> AdCopy:
        """Parse Gemini response into an AdCopy entity."""
        lines = {}
        for line in text.strip().split("\n"):
            if ":" in line:
                key, _, value = line.partition(":")
                lines[key.strip().upper()] = value.strip()

        return AdCopy(
            platform=platform,
            headline=lines.get("HEADLINE", "")[:30 if platform == AdPlatform.GOOGLE else 100],
            description=lines.get("DESCRIPTION", "")[:90] if platform == AdPlatform.GOOGLE else lines.get("DESCRIPTION", ""),
            call_to_action=lines.get("CTA", "Compra Ahora"),
        )
