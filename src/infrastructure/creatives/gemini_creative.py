"""Gemini-based creative generator.

Uses Gemini's image generation to create product ad creatives
from a product photo + marketing data.
"""

from __future__ import annotations

import asyncio
import base64
import httpx
from pathlib import Path

from google import genai
from google.genai import types

from src.shared.config import get_gemini_settings
from src.shared.logger import logger


class GeminiCreativeGenerator:
    """Generate product ad creatives using Gemini image generation."""

    def __init__(self) -> None:
        settings = get_gemini_settings()
        self._client = genai.Client(api_key=settings.api_key.get_secret_value())
        self._model = "gemini-3.1-flash-image"

    async def generate(
        self,
        *,
        product_image_url: str,
        product_name: str,
        headline: str,
        benefits: list[str],
        price: float,
        category: str = "",
        style: str = "professional dark background with golden accents",
        output_path: str | None = None,
    ) -> str | None:
        """Generate a creative ad image using Gemini.

        Args:
            product_image_url: URL of the product photo.
            product_name: Product name for context.
            headline: Marketing headline.
            benefits: Key benefits to highlight.
            price: Sale price.
            category: Product category.
            style: Visual style description.
            output_path: Where to save. Auto-generated if None.

        Returns:
            Path to generated image, or None if generation failed.
        """
        # Download product image
        image_bytes = await self._download_image(product_image_url)
        if not image_bytes:
            logger.warning("[GeminiCreative] Failed to download product image")
            return None

        benefits_text = ", ".join(benefits[:3])

        prompt = f"""Create a professional e-commerce product advertisement image.

REQUIREMENTS:
- Place the product photo prominently in the center on a {style}
- Add text overlay with the headline: "{headline}"
- Add 3 benefit bullets: {benefits_text}
- Add a price badge showing "${price:.2f}"
- Add "Envio Gratis" badge
- Style: premium, dark background, clean typography
- The product should look premium and professional
- Text in Spanish
- NO watermarks, NO stock photo marks
- Format: vertical 1080x1920 or square 1080x1080

PRODUCT: {product_name} (category: {category})
"""

        try:
            logger.info(f"[GeminiCreative] Generating creative for: {product_name}")

            response = await asyncio.to_thread(
                self._client.models.generate_content,
                model=self._model,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                ),
            )

            # Extract generated image
            if not output_path:
                output_dir = Path("frontend/src/data/creatives")
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = str(output_dir / f"gemini_{hash(headline) % 100000}.png")

            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.mime_type.startswith("image/"):
                    image_data = part.inline_data.data
                    Path(output_path).write_bytes(image_data)
                    logger.info(f"[GeminiCreative] Saved creative: {output_path}")
                    return output_path

            logger.warning("[GeminiCreative] No image in response")
            return None

        except Exception as e:
            logger.error(f"[GeminiCreative] Generation failed: {e}")
            return None

    async def _download_image(self, url: str) -> bytes | None:
        """Download an image from URL."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    return resp.content
        except Exception as e:
            logger.warning(f"[GeminiCreative] Image download failed: {e}")
        return None
