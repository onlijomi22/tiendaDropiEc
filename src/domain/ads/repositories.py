"""Ads repository interface.

Spec: specs/ads/campaign.spec.md
"""

from abc import ABC, abstractmethod
from src.domain.ads.entities import AdCopy, Campaign, CampaignMetrics, AdPlatform


class IAdsRepository(ABC):
    """Abstract repository for ad campaign operations.

    Implementations:
        - GoogleAdsRepository (infrastructure/google_ads/)
        - TikTokAdsRepository (infrastructure/tiktok_ads/)
    """

    @abstractmethod
    async def create_campaign(
        self, product_id: str, copy: AdCopy, daily_budget_usd: float
    ) -> Campaign:
        """Create a new ad campaign for a product.

        Args:
            product_id: Dropi product ID to advertise.
            copy: Ad copy (headline, description, CTA).
            daily_budget_usd: Daily budget in USD.

        Returns:
            Created Campaign with platform-assigned ID.

        Raises:
            AdsAPIError: If the platform API call fails.
        """

    @abstractmethod
    async def pause_campaign(self, campaign_id: str) -> None:
        """Pause an active campaign.

        Args:
            campaign_id: The campaign ID to pause.

        Raises:
            AdsAPIError: If the platform API call fails.
        """

    @abstractmethod
    async def get_metrics(
        self, campaign_id: str, period_days: int = 7
    ) -> CampaignMetrics:
        """Retrieve performance metrics for a campaign.

        Args:
            campaign_id: Campaign ID.
            period_days: Number of days to look back.

        Returns:
            CampaignMetrics for the requested period.

        Raises:
            AdsAPIError: If metrics cannot be retrieved.
        """

    @abstractmethod
    async def list_active_campaigns(self) -> list[Campaign]:
        """Return all currently active campaigns.

        Returns:
            List of active Campaign entities.
        """
