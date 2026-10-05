"""Template-based creative generator using Playwright screenshots.

Takes product data + HTML template → renders → screenshots to produce
professional-looking product cards for ads and landing pages.

Deterministic output — no AI randomness.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

from src.shared.logger import logger

_TEMPLATE_DIR = Path(__file__).resolve().parents[2] / ".." / "scripts" / "creative_templates"

# Size presets
SIZES = {
    "feed": (1080, 1080),       # Instagram/Facebook feed
    "story": (1080, 1920),      # TikTok/Instagram story
    "meta_ad": (1200, 628),     # Meta Ads landscape
}

# Responsive values per size
_RESPONSIVE = {
    "feed": {
        "PADDING": 40, "HEADLINE_SIZE": 36, "SUB_SIZE": 16, "SUB_MARGIN": 16,
        "BENEFIT_GAP": 8, "BENEFIT_MARGIN": 16, "BENEFIT_SIZE": 16,
        "CHECK_SIZE": 22, "CHECK_FONT": 12, "PRICE_PAD_V": 12, "PRICE_PAD_H": 24,
        "PRICE_LABEL_SIZE": 12, "PRICE_SIZE": 36, "TRUST_SIZE": 12, "BADGE_SIZE": 12,
    },
    "story": {
        "PADDING": 48, "HEADLINE_SIZE": 42, "SUB_SIZE": 18, "SUB_MARGIN": 20,
        "BENEFIT_GAP": 12, "BENEFIT_MARGIN": 24, "BENEFIT_SIZE": 18,
        "CHECK_SIZE": 26, "CHECK_FONT": 14, "PRICE_PAD_V": 16, "PRICE_PAD_H": 32,
        "PRICE_LABEL_SIZE": 14, "PRICE_SIZE": 44, "TRUST_SIZE": 14, "BADGE_SIZE": 14,
    },
    "meta_ad": {
        "PADDING": 32, "HEADLINE_SIZE": 28, "SUB_SIZE": 14, "SUB_MARGIN": 12,
        "BENEFIT_GAP": 6, "BENEFIT_MARGIN": 12, "BENEFIT_SIZE": 14,
        "CHECK_SIZE": 18, "CHECK_FONT": 10, "PRICE_PAD_V": 10, "PRICE_PAD_H": 20,
        "PRICE_LABEL_SIZE": 10, "PRICE_SIZE": 28, "TRUST_SIZE": 11, "BADGE_SIZE": 11,
    },
}

# Color palettes
_PALETTES = {
    "pink": {"ACCENT_COLOR": "#FD2C77", "ACCENT_DARK": "#c41e5c"},
    "blue": {"ACCENT_COLOR": "#1e20ca", "ACCENT_DARK": "#15179a"},
    "green": {"ACCENT_COLOR": "#2f734a", "ACCENT_DARK": "#1f5435"},
    "orange": {"ACCENT_COLOR": "#ff6b35", "ACCENT_DARK": "#cc5528"},
    "purple": {"ACCENT_COLOR": "#85457a", "ACCENT_DARK": "#6b3562"},
    "gold": {"ACCENT_COLOR": "#d4a036", "ACCENT_DARK": "#b8891e"},
}


class TemplateRenderer:
    """Renders product creatives from HTML templates via Playwright."""

    async def render(
        self,
        *,
        headline: str,
        subheadline: str,
        product_image_url: str,
        price: float,
        benefits: list[str],
        trust_signals: list[str],
        size: str = "feed",
        palette: str = "gold",
        output_path: str | None = None,
    ) -> str:
        """Render a product card creative.

        Args:
            headline: Main headline (benefit, not product name).
            subheadline: Supporting text.
            product_image_url: URL of the product image.
            price: Sale price.
            benefits: 3-5 short benefits.
            trust_signals: Trust badges text.
            size: One of 'feed', 'story', 'meta_ad'.
            palette: Color palette name.
            output_path: Where to save the PNG. Auto-generated if None.

        Returns:
            Path to the generated PNG file.
        """
        width, height = SIZES.get(size, SIZES["feed"])
        responsive = _RESPONSIVE.get(size, _RESPONSIVE["feed"])
        colors = _PALETTES.get(palette, _PALETTES["gold"])

        # Build benefits HTML
        benefits_html = "\n".join(
            f'<div class="benefit"><span class="benefit-check">✓</span><span>{b}</span></div>'
            for b in benefits[:4]
        )

        # Build trust signals HTML
        trust_icons = ["🚚", "💵", "🔒", "⭐", "✅"]
        trust_html = "\n".join(
            f'<div class="trust-item"><span class="trust-icon">{trust_icons[i % len(trust_icons)]}</span>{s}</div>'
            for i, s in enumerate(trust_signals[:4])
        )

        # Load and populate template
        template_path = _TEMPLATE_DIR / "product_card.html"
        template = template_path.read_text(encoding="utf-8")

        replacements = {
            "{{WIDTH}}": str(width),
            "{{HEIGHT}}": str(height),
            "{{HEADLINE}}": headline,
            "{{SUBHEADLINE}}": subheadline,
            "{{PRODUCT_IMAGE}}": product_image_url,
            "{{PRICE}}": f"{price:.2f}",
            "{{BENEFITS_HTML}}": benefits_html,
            "{{TRUST_HTML}}": trust_html,
            **{f"{{{{{k}}}}}": str(v) for k, v in responsive.items()},
            **{f"{{{{{k}}}}}": str(v) for k, v in colors.items()},
        }

        html = template
        for key, value in replacements.items():
            html = html.replace(key, value)

        # Render with Playwright
        if not output_path:
            output_dir = Path("frontend/src/data/creatives")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = str(output_dir / f"creative_{size}_{hash(headline) % 100000}.png")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.set_content(html, wait_until="networkidle")
            await page.wait_for_timeout(1000)  # Wait for image to load
            await page.screenshot(path=output_path, type="png")
            await browser.close()

        logger.info(f"[TemplateRenderer] Generated {size} creative: {output_path}")
        return output_path
