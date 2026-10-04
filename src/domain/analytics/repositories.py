"""Analytics repository interface.

Spec: specs/analytics/report.spec.md
"""

from abc import ABC, abstractmethod
from datetime import date
from src.domain.analytics.entities import Anomaly, SalesReport


class IAnalyticsRepository(ABC):
    """Abstract repository for analytics data."""

    @abstractmethod
    async def get_sales_report(self, start: date, end: date) -> SalesReport:
        """Fetch sales data for a date range from Dropi.

        Args:
            start: Start date (inclusive).
            end: End date (inclusive).

        Returns:
            SalesReport for the period.

        Raises:
            DropiScrapingError: If data cannot be scraped.
        """

    @abstractmethod
    async def get_historical_orders_avg(self, days: int = 7) -> float:
        """Get average daily orders over the last N days.

        Args:
            days: Number of historical days to average.

        Returns:
            Average daily order count.
        """

    @abstractmethod
    async def save_anomaly(self, anomaly: Anomaly) -> None:
        """Persist a detected anomaly for record-keeping.

        Args:
            anomaly: The detected Anomaly to save.
        """
