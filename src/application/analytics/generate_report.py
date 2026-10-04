"""Use case: Generate a sales report and detect anomalies.

Spec: specs/analytics/report.spec.md
Criteria: CA-ANAL-01, CA-ANAL-02
"""

from dataclasses import dataclass
from datetime import date, timedelta
from src.domain.analytics.entities import Anomaly, AnomalyType, AnomalySeverity, SalesReport
from src.domain.analytics.repositories import IAnalyticsRepository
from src.domain.business_rules import ANOMALY_DROP_THRESHOLD_PCT
from src.shared.logger import logger


@dataclass
class GenerateReportInput:
    """Input DTO for report generation."""
    start: date
    end: date
    detect_anomalies: bool = True


@dataclass
class GenerateReportOutput:
    """Output DTO with report and optional anomalies."""
    report: SalesReport
    anomalies: list[Anomaly]


class GenerateReportUseCase:
    """Generate a period sales report and detect business anomalies.

    Args:
        analytics_repo: Repository for Dropi analytics data.
    """

    def __init__(self, analytics_repo: IAnalyticsRepository) -> None:
        self._repo = analytics_repo

    async def execute(self, input_data: GenerateReportInput) -> GenerateReportOutput:
        """Generate report and detect anomalies."""
        report = await self._repo.get_sales_report(input_data.start, input_data.end)
        logger.info(
            f"Report {input_data.start}→{input_data.end}: "
            f"{report.total_orders} orders, "
            f"delivery rate {report.delivery_rate:.1%}"
        )

        anomalies: list[Anomaly] = []
        if input_data.detect_anomalies:
            anomalies = await self._detect_anomalies(report)

        return GenerateReportOutput(report=report, anomalies=anomalies)

    async def _detect_anomalies(self, report: SalesReport) -> list[Anomaly]:
        """Check for anomalies per CA-ANAL-02."""
        anomalies = []
        avg_daily = await self._repo.get_historical_orders_avg(days=7)
        period_days = (report.period_end - report.period_start).days + 1
        avg_for_period = avg_daily * period_days

        if avg_for_period > 0:
            drop_pct = (avg_for_period - report.total_orders) / avg_for_period * 100
            if drop_pct >= ANOMALY_DROP_THRESHOLD_PCT:
                anomaly = Anomaly(
                    type=AnomalyType.DROP,
                    metric="total_orders",
                    value=float(report.total_orders),
                    expected_value=avg_for_period,
                    severity=AnomalySeverity.HIGH,
                )
                await self._repo.save_anomaly(anomaly)
                anomalies.append(anomaly)
                logger.warning(
                    f"[CA-ANAL-02] Order drop detected: {drop_pct:.1f}% below 7-day avg"
                )

        return anomalies
