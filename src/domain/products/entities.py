"""Product domain entities.

Defined from specs/products/product.spec.md.
All entities use Pydantic v2 for validation and serialization.
No infrastructure dependencies — pure domain objects.
"""

from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from src.domain.business_rules import (
    MIN_MARGIN_PCT,
    MIN_STOCK_FOR_BUY,
    SCORE_BUY_THRESHOLD,
    SCORE_WATCH_THRESHOLD,
    MAX_PRODUCTS_PER_RUN,
)
from src.shared.exceptions import SpecViolationError


class CompetitionLevel(str, Enum):  # noqa: N818
    """Competition level for a product in the market."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ProductRecommendation(str, Enum):
    """Agent recommendation for whether to sell a product."""
    BUY = "BUY"
    SKIP = "SKIP"
    WATCH = "WATCH"


class ProductLifecycle(str, Enum):
    """Full product lifecycle for tracking and analytics."""
    DISCOVERED = "DISCOVERED"       # Scraped from Dropi
    FILTERED = "FILTERED"           # Passed initial scoring (BUY)
    RESEARCHING = "RESEARCHING"     # V2 enrichment in progress
    VALIDATED = "VALIDATED"         # Enriched and reviewed by operator
    READY_FOR_TEST = "READY_FOR_TEST"  # Landing published, waiting for ads
    TESTING = "TESTING"             # Ads running, collecting data
    WINNER = "WINNER"               # Profitable, scaling
    SCALING = "SCALING"             # Budget increased
    PAUSED = "PAUSED"               # Temporarily stopped
    REJECTED = "REJECTED"           # Not viable after analysis
    EXHAUSTED = "EXHAUSTED"         # Market saturated or stock depleted


class Product(BaseModel):
    """Dropi product entity.

    Spec: specs/products/product.spec.md#entities
    """

    id: str = Field(description="Unique product ID in Dropi")
    name: str = Field(min_length=1, description="Product name")
    category: str = Field(min_length=1, description="Dropi category")
    dropi_price: float = Field(gt=0, description="Cost price in Dropi (USD)")
    suggested_price: float = Field(gt=0, description="Suggested retail price (USD)")
    stock: int = Field(ge=0, description="Available units")
    supplier_id: str = Field(description="Supplier ID")
    supplier_name: str = Field(default="Importadora Desconocida", description="Supplier Store Name")
    images: list[str] = Field(min_length=1, description="Product image URLs")
    description: str = Field(min_length=1, description="Product description")
    weight_kg: float | None = Field(default=None, ge=0, description="Weight in kg")
    tags: list[str] = Field(default_factory=list, description="Product tags")

    @field_validator("suggested_price")
    @classmethod
    def price_must_exceed_cost(cls, v: float, info) -> float:
        """Ensure suggested price is higher than Dropi cost."""
        if hasattr(info, 'data') and 'dropi_price' in info.data:
            if v <= info.data['dropi_price']:
                raise ValueError(
                    f"suggested_price ({v}) must be greater than dropi_price ({info.data['dropi_price']})"
                )
        return v

    @property
    def margin_pct(self) -> float:
        """Calculate gross margin percentage.

        Formula from CA-PROD-01:
            margin = (selling_price - dropi_price) / selling_price * 100
        """
        return (self.suggested_price - self.dropi_price) / self.suggested_price * 100


class ProductScore(BaseModel):
    """AI-generated score for a product.

    Spec: specs/products/product.spec.md#entities (ProductScore)
    All thresholds are enforced via model_validator from spec constants.
    """

    product_id: str = Field(description="Reference to Product.id")
    margin_pct: float = Field(ge=0, le=100, description="Gross margin %")
    competition_level: CompetitionLevel = Field(description="Market competition level")
    trend_score: float = Field(ge=0.0, le=1.0, description="Trend score 0.0-1.0")

    @field_validator("competition_level", mode="before")
    @classmethod
    def normalize_competition_level(cls, v: str) -> str:
        """Accept legacy 'MED' value from serialized data."""
        if v == "MED":
            return "MEDIUM"
        return v
    total_score: float = Field(ge=0.0, le=100.0, description="Final score 0-100")
    recommendation: ProductRecommendation = Field(description="Agent recommendation")
    reasoning: str = Field(min_length=10, description="Agent reasoning for the score")

    @model_validator(mode="after")
    def validate_recommendation_matches_score(self) -> "ProductScore":
        """Enforce spec CA-PROD-02: recommendation must match total_score thresholds."""
        score = self.total_score
        rec = self.recommendation

        if score >= SCORE_BUY_THRESHOLD and rec != ProductRecommendation.BUY:
            raise SpecViolationError(
                "CA-PROD-02",
                f"Score {score} >= {SCORE_BUY_THRESHOLD} requires BUY, got {rec}"
            )
        if SCORE_WATCH_THRESHOLD <= score < SCORE_BUY_THRESHOLD and rec != ProductRecommendation.WATCH:
            raise SpecViolationError(
                "CA-PROD-02",
                f"Score {score} in WATCH range requires WATCH, got {rec}"
            )
        if score < SCORE_WATCH_THRESHOLD and rec != ProductRecommendation.SKIP:
            raise SpecViolationError(
                "CA-PROD-02",
                f"Score {score} < {SCORE_WATCH_THRESHOLD} requires SKIP, got {rec}"
            )
        return self
