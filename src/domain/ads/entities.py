"""Ads domain entities.

Defined from specs/ads/campaign.spec.md.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator
from src.domain.business_rules import (
    INITIAL_DAILY_BUDGET_USD,
    SCALE_BUDGET_USD,
    SCALE_ROAS_THRESHOLD,
    PAUSE_ROAS_THRESHOLD,
    PAUSE_DAYS_MIN,
    GOOGLE_HEADLINE_MAX_CHARS,
    GOOGLE_DESCRIPTION_MAX_CHARS,
)
from src.shared.exceptions import SpecViolationError


class AdPlatform(str, Enum):
    """Supported advertising platforms."""
    GOOGLE = "GOOGLE"
    TIKTOK = "TIKTOK"


class CampaignStatus(str, Enum):
    """Campaign lifecycle status."""
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ENDED = "ENDED"


class AdCopy(BaseModel):
    """Ad copy content for a specific platform.

    Spec: specs/ads/campaign.spec.md#adcopy
    Character limits enforced per CA-ADS-01.
    """

    platform: AdPlatform
    headline: str = Field(min_length=1, description="Main headline")
    description: str = Field(min_length=1, description="Ad description")
    call_to_action: str = Field(description="CTA text")

    @field_validator("headline")
    @classmethod
    def validate_headline_length(cls, v: str, info) -> str:
        """Enforce CA-ADS-01: platform-specific headline limits."""
        platform = info.data.get("platform")
        if platform == AdPlatform.GOOGLE and len(v) > GOOGLE_HEADLINE_MAX_CHARS:
            raise SpecViolationError(
                "CA-ADS-01",
                f"Google headline exceeds {GOOGLE_HEADLINE_MAX_CHARS} chars: '{v}' ({len(v)} chars)"
            )
        return v

    @field_validator("description")
    @classmethod
    def validate_description_length(cls, v: str, info) -> str:
        """Enforce CA-ADS-01: Google description max chars."""
        platform = info.data.get("platform")
        if platform == AdPlatform.GOOGLE and len(v) > GOOGLE_DESCRIPTION_MAX_CHARS:
            raise SpecViolationError(
                "CA-ADS-01",
                f"Google description exceeds {GOOGLE_DESCRIPTION_MAX_CHARS} chars ({len(v)} chars)"
            )
        return v


class Campaign(BaseModel):
    """Advertising campaign entity.

    Spec: specs/ads/campaign.spec.md#campaign
    """

    id: str = Field(description="Campaign ID in the ad platform")
    platform: AdPlatform
    product_id: str = Field(description="Dropi product ID being advertised")
    name: str = Field(min_length=1)
    daily_budget_usd: float = Field(gt=0, description="Daily budget in USD")
    status: CampaignStatus = Field(default=CampaignStatus.ACTIVE)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CampaignMetrics(BaseModel):
    """Performance metrics for a campaign.

    Spec: specs/ads/campaign.spec.md#campaignmetrics
    """

    campaign_id: str
    impressions: int = Field(ge=0)
    clicks: int = Field(ge=0)
    conversions: int = Field(ge=0)
    spend_usd: float = Field(ge=0)
    roas: float = Field(ge=0, description="Return on Ad Spend")
    period_days: int = Field(ge=1)

    @property
    def ctr(self) -> float:
        """Click-through rate (clicks / impressions)."""
        if self.impressions == 0:
            return 0.0
        return self.clicks / self.impressions

    @property
    def should_pause(self) -> bool:
        """Check CA-ADS-02: whether this campaign should be paused."""
        return self.roas < PAUSE_ROAS_THRESHOLD and self.period_days >= PAUSE_DAYS_MIN
