"""Product Enrichment domain entities.

Every piece of product data carries its origin, confidence, and type.
The landing page only consumes EnrichedProduct — never raw Dropi/ML/Gemini data.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

from src.domain.products.entities import CompetitionLevel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class DataOrigin(str, Enum):
    """Source system that produced a piece of data."""
    DROPI = "DROPI"
    MERCADOLIBRE = "MERCADOLIBRE"
    GOOGLE_SEARCH = "GOOGLE_SEARCH"
    LLM_INFERENCE = "LLM_INFERENCE"
    MANUAL = "MANUAL"


class DataType(str, Enum):
    """Classification of how a piece of data was produced."""
    FACT = "FACT"
    DERIVED_FACT = "DERIVED_FACT"
    DERIVED_BENEFIT = "DERIVED_BENEFIT"
    MARKETING_COPY = "MARKETING_COPY"
    PLACEHOLDER = "PLACEHOLDER"


class MatchQuality(str, Enum):
    """How confident we are that an external listing is the SAME product."""
    EXACT = "EXACT"          # Same SKU / name / image. Confidence >= 0.9
    SIMILAR = "SIMILAR"      # Same type, similar specs. 0.5-0.89
    CATEGORY_ONLY = "CATEGORY_ONLY"  # Only share category. < 0.5


# ---------------------------------------------------------------------------
# Evidence
# ---------------------------------------------------------------------------

class ProductEvidence(BaseModel):
    """A single piece of evidence about a product, with full traceability."""

    field: str = Field(description="What field this describes: price, review, benefit, image_url, etc.")
    value: Any = Field(description="The data itself")
    data_type: DataType
    origin: DataOrigin
    confidence: float = Field(ge=0.0, le=1.0)
    source_url: str | None = None
    source_product_id: str | None = None
    match_quality: MatchQuality | None = None
    collected_at: datetime = Field(default_factory=datetime.utcnow)
    notes: str = ""


class MatchResult(BaseModel):
    """Result of matching a Dropi product against an external listing."""
    quality: MatchQuality
    match_score: float = Field(ge=0.0, le=1.0)
    name_similarity: float = Field(ge=0.0, le=1.0)
    price_compatible: bool
    reasoning: str


# ---------------------------------------------------------------------------
# Enriched sub-models
# ---------------------------------------------------------------------------

class ProductImage(BaseModel):
    """An image with quality assessment."""
    url: str
    origin: DataOrigin = DataOrigin.DROPI
    is_clean: bool = False
    is_product_only: bool = False
    has_chinese_text: bool = False
    has_phone_number: bool = False
    width: int | None = None
    height: int | None = None
    priority: int = 0


class ProductSpec(BaseModel):
    """A single product specification extracted from description."""
    name: str
    value: str
    data_type: DataType = DataType.DERIVED_FACT
    confidence: float = Field(ge=0.0, le=1.0, default=0.6)


class EvidencedClaim(BaseModel):
    """A claim about the product backed by evidence."""
    text: str
    data_type: DataType
    confidence: float = Field(ge=0.0, le=1.0)
    source_url: str | None = None
    origin: DataOrigin


class ProductCopy(BaseModel):
    """Marketing copy — explicitly separated from facts. Always MARKETING_COPY."""
    headline: str
    subheadline: str
    tiktok_hook: str = ""
    tiktok_script: str = ""
    meta_headline: str = ""
    meta_body: str = ""
    objection_handlers: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Category config
# ---------------------------------------------------------------------------

class CategoryConfig(BaseModel):
    """Visual and behavioral configuration per product category."""
    slug: str
    display_name: str
    theme_color: str = "blue"
    tone: str = "practical"
    primary_objection: str = "Es de buena calidad?"
    trust_signals: list[str] = Field(default_factory=list)
    price_range_min: float = 10.0
    price_range_max: float = 60.0
    typical_margin_pct: float = 40.0
    min_clean_images: int = 2
    prefer_lifestyle_images: bool = False
    show_comparison_table: bool = True
    show_reviews_section: bool = True
    show_specs_table: bool = False
    show_faq: bool = True


# ---------------------------------------------------------------------------
# EnrichedProduct — the final model the landing page consumes
# ---------------------------------------------------------------------------

class EnrichedProduct(BaseModel):
    """Product with validated, confidence-scored data ready for the landing page."""

    # Identity
    product_id: str
    dropi_name: str
    display_name: str
    category: str
    slug: str

    # Pricing
    dropi_price: float
    sale_price: float
    competitor_avg_price: float | None = None
    competitor_price_confidence: float = 0.0

    # Stock & Supplier
    stock: int
    supplier_name: str
    supplier_id: str

    # Images
    images: list[ProductImage] = Field(default_factory=list)

    # Description
    description_raw: str
    description_clean: str = ""
    specifications: list[ProductSpec] = Field(default_factory=list)

    # Market evidence
    buyer_concerns: list[EvidencedClaim] = Field(default_factory=list)
    buyer_positives: list[EvidencedClaim] = Field(default_factory=list)
    real_reviews: list[EvidencedClaim] = Field(default_factory=list)
    competition_level: CompetitionLevel = CompetitionLevel.MEDIUM
    competition_count: int = 0

    # Benefits
    benefits: list[EvidencedClaim] = Field(default_factory=list)

    # Marketing copy (may not exist yet)
    marketing_copy: ProductCopy | None = None

    # Viability
    viable: bool = False
    viability_reason: str = ""
    margin_pct: float = 0.0
    net_profit: float = 0.0

    # Meta
    enriched_at: datetime = Field(default_factory=datetime.utcnow)
    evidence_count: int = 0
    avg_confidence: float = 0.0
    human_review_notes: list[str] = Field(default_factory=list)
    category_config: CategoryConfig | None = None

    @property
    def clean_images(self) -> list[ProductImage]:
        """Only images suitable for the landing page."""
        return [img for img in self.images if img.is_clean and img.is_product_only]

    @property
    def has_sufficient_images(self) -> bool:
        min_required = self.category_config.min_clean_images if self.category_config else 2
        return len(self.clean_images) >= min_required

    @property
    def displayable_reviews(self) -> list[EvidencedClaim]:
        """Only reviews with sufficient confidence to show as customer reviews."""
        return [r for r in self.real_reviews if r.confidence >= 0.7]

    @property
    def displayable_benefits(self) -> list[EvidencedClaim]:
        """Only benefits with sufficient confidence."""
        return [b for b in self.benefits if b.confidence >= 0.4]
