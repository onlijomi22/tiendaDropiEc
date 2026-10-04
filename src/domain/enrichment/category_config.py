"""Category configuration loader from config/categories.yaml."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

from src.domain.enrichment.entities import CategoryConfig


_CONFIG_PATH = Path(__file__).resolve().parents[3] / "config" / "categories.yaml"


@lru_cache(maxsize=1)
def _load_raw() -> dict:
    """Load and cache the raw YAML."""
    with open(_CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def get_category_config(category: str) -> CategoryConfig:
    """Get configuration for a product category.

    Falls back to default config if category not found.
    Category matching is case-insensitive and stripped.

    Args:
        category: Category name (e.g. 'cocina', 'Hogar', 'BELLEZA').

    Returns:
        CategoryConfig for the category.
    """
    raw = _load_raw()
    key = category.lower().strip()
    categories = raw.get("categories", {})
    default = raw.get("default", {})

    data = categories.get(key, default)
    slug = key.replace(" ", "-")

    return CategoryConfig(
        slug=slug,
        display_name=data.get("display_name", category.title()),
        theme_color=data.get("theme_color", "blue"),
        tone=data.get("tone", "practical"),
        primary_objection=data.get("primary_objection", "Es de buena calidad?"),
        trust_signals=data.get("trust_signals", []),
        price_range_min=data.get("price_range_min", 10.0),
        price_range_max=data.get("price_range_max", 60.0),
        typical_margin_pct=data.get("typical_margin_pct", 40.0),
        min_clean_images=data.get("min_clean_images", 2),
        prefer_lifestyle_images=data.get("prefer_lifestyle_images", False),
        show_comparison_table=data.get("show_comparison_table", True),
        show_reviews_section=data.get("show_reviews_section", True),
        show_specs_table=data.get("show_specs_table", False),
        show_faq=data.get("show_faq", True),
    )
