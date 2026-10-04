"""Product Intelligence domain entities.

Spec: specs/intelligence/product_intelligence.spec.md

All market data must come from real web sources.
No hallucinated competitor prices or buyer reviews.
"""

from __future__ import annotations
from pydantic import BaseModel, Field
from src.domain.products.entities import CompetitionLevel  # noqa: F401 — re-export for backward compat


class CompetitorListing(BaseModel):
    """A competing product listing found on MercadoLibre Ecuador."""
    title: str = Field(description="Product listing title")
    price_usd: float = Field(ge=0, description="Sale price in USD")
    sales_count: int = Field(default=0, ge=0, description="Number of sales")
    rating: float = Field(default=0.0, ge=0, le=5, description="Rating 0-5")
    url: str = Field(description="Listing URL")


class MarketInsight(BaseModel):
    """Real market data for a product category. All fields backed by sources.

    Spec: CA-INTEL-01, CA-INTEL-02
    """
    category: str
    product_name: str
    buyer_concerns: list[str] = Field(
        default_factory=list,
        description="Real pre-purchase fears from buyers (sourced)"
    )
    buyer_positives: list[str] = Field(
        default_factory=list,
        description="What buyers actually praise (sourced)"
    )
    real_reviews: list[str] = Field(
        default_factory=list,
        description="Exact quotes or real reviews from the web"
    )
    competitors: list[CompetitorListing] = Field(default_factory=list)
    avg_competitor_price: float = Field(default=0.0)
    competition_count: int = Field(default=0)
    competition_level: CompetitionLevel = Field(default=CompetitionLevel.MEDIUM)
    sources: list[str] = Field(
        default_factory=list,
        description="URLs used as data sources"
    )
    search_query_used: str = Field(default="", description="The query that was searched")


class ProductCopyDraft(BaseModel):
    """AI-generated copy draft based on real market data. Ready for human review.

    Spec: CA-INTEL-03
    """
    product_id: str
    product_name: str

    # Landing page copy
    landing_headline: str = Field(description="Main headline, max 60 chars")
    landing_subheadline: str = Field(description="Supporting headline, max 120 chars")
    benefits: list[str] = Field(
        description="3-5 benefits based on real buyer positives"
    )
    review_quotes: list[str] = Field(
        description="2-3 review-style quotes inspired by real data, clearly labeled as illustrative"
    )
    objection_handlers: list[str] = Field(
        description="Responses to real buyer concerns"
    )
    comparison_items: list[dict] = Field(
        default_factory=list,
        description="List of dicts with keys: feature (str), ourProduct (bool), others (bool)"
    )
    stat_metrics: list[dict] = Field(
        default_factory=list,
        description="List of dicts with keys: percentage (str, e.g. '95%'), text (str)"
    )

    # Ad copy
    tiktok_hook: str = Field(description="First 3 seconds of TikTok video")
    tiktok_script: str = Field(description="Full 30-second TikTok script")
    meta_headline: str = Field(description="Ad headline for Meta", max_length=40)
    meta_body: str = Field(description="Ad body for Meta", max_length=125)
    
    is_bulky: bool = Field(default=False, description="True if the product is large, heavy, or furniture")

    # Pricing
    suggested_price_usd: float = Field(
        description="Recommended sale price based on competition + margin"
    )
    suggested_margin_pct: float

    # Transparency
    data_sources: list[str] = Field(description="Sources used to generate this copy")
    human_review_notes: str = Field(
        description="What the human operator should verify before publishing"
    )


class ProductIntelligenceResult(BaseModel):
    """Combined output: raw data + draft copy. Spec CA-INTEL-03."""
    product_id: str
    product_name: str
    dropi_cost: float
    # Raw data (always shown)
    market_insight: MarketInsight
    # Draft copy (always generated, ready for human review)
    copy_draft: ProductCopyDraft
    # Quick assessment
    viable: bool = Field(description="True if margin + competition make this worth selling")
    viability_reason: str
