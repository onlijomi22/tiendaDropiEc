"""Analytics domain entities.

Spec: specs/analytics/report.spec.md
"""

from datetime import date, datetime
from enum import Enum
from pydantic import BaseModel, Field, model_validator


class AnomalyType(str, Enum):
    """Type of anomaly detected."""
    DROP = "DROP"    # Significant decrease
    SPIKE = "SPIKE"  # Significant increase
    STALE = "STALE"  # No activity for too long


class AnomalySeverity(str, Enum):
    """Severity level of an anomaly."""
    LOW = "LOW"
    MEDIUM = "MED"
    HIGH = "HIGH"


class SalesReport(BaseModel):
    """Daily or weekly sales report from Dropi.

    Spec: specs/analytics/report.spec.md#salesreport
    """

    period_start: date
    period_end: date
    total_orders: int = Field(ge=0)
    delivered_orders: int = Field(ge=0)
    cancelled_orders: int = Field(ge=0)
    gross_revenue: float = Field(ge=0, description="Gross revenue in USD")
    net_profit: float = Field(description="Net profit in USD")
    top_products: list[str] = Field(default_factory=list, description="Top product IDs")

    @model_validator(mode="after")
    def validate_order_totals(self) -> "SalesReport":
        """Ensure delivered + cancelled <= total_orders."""
        if self.delivered_orders + self.cancelled_orders > self.total_orders:
            raise ValueError(
                f"delivered ({self.delivered_orders}) + cancelled ({self.cancelled_orders}) "
                f"cannot exceed total_orders ({self.total_orders})"
            )
        return self

    @property
    def delivery_rate(self) -> float:
        """Calculate delivery success rate (CA-ANAL-01).

        Returns:
            Delivery rate 0.0-1.0. Returns 0.0 if no orders.
        """
        if self.total_orders == 0:
            return 0.0
        return self.delivered_orders / self.total_orders


class Anomaly(BaseModel):
    """A detected anomaly in business metrics.

    Spec: specs/analytics/report.spec.md#anomaly
    """

    type: AnomalyType
    metric: str = Field(description="Name of the affected metric")
    value: float = Field(description="Current actual value")
    expected_value: float = Field(description="Expected baseline value")
    severity: AnomalySeverity
    detected_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def deviation_pct(self) -> float:
        """Calculate percentage deviation from expected value."""
        if self.expected_value == 0:
            return 0.0
        return abs(self.value - self.expected_value) / self.expected_value * 100
