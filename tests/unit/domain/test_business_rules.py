"""Unit tests for business rules coherence.

Validates that centralized business constants maintain
internal consistency and expected relationships.
"""

from src.domain.business_rules import (
    MIN_MARGIN_PCT,
    TARGET_MARGIN_PCT,
    SCORE_BUY_THRESHOLD,
    SCORE_WATCH_THRESHOLD,
    MIN_STOCK_FOR_BUY,
    STOCK_ALERT_THRESHOLD,
    MARGIN_WEIGHT,
    TREND_WEIGHT,
    COMPETITION_WEIGHT,
    ESTIMATED_SHIPPING_COST_USD,
    ESTIMATED_CPA_USD,
    TARGET_PROFIT_USD,
    ROAS_ALERT_THRESHOLD,
    PAUSE_ROAS_THRESHOLD,
    SCALE_ROAS_THRESHOLD,
    COMPETITION_LOW_MAX_SELLERS,
    COMPETITION_HIGH_MIN_SELLERS,
)
from src.domain.products.entities import CompetitionLevel, ProductScore, ProductRecommendation


class TestBusinessRulesCoherence:
    """Ensure business rule constants are internally consistent."""

    def test_margin_thresholds_ordered(self):
        """MIN_MARGIN_PCT must be strictly less than TARGET_MARGIN_PCT."""
        assert MIN_MARGIN_PCT < TARGET_MARGIN_PCT

    def test_score_thresholds_ordered(self):
        """WATCH threshold must be strictly less than BUY threshold."""
        assert SCORE_WATCH_THRESHOLD < SCORE_BUY_THRESHOLD

    def test_stock_thresholds_ordered(self):
        """STOCK_ALERT must be strictly less than MIN_STOCK_FOR_BUY."""
        assert STOCK_ALERT_THRESHOLD < MIN_STOCK_FOR_BUY

    def test_roas_thresholds_ordered(self):
        """ROAS thresholds: alert < pause < scale."""
        assert ROAS_ALERT_THRESHOLD < PAUSE_ROAS_THRESHOLD < SCALE_ROAS_THRESHOLD

    def test_scoring_weights_sum_to_100(self):
        """Margin + trend + competition weights must equal 100."""
        assert MARGIN_WEIGHT + TREND_WEIGHT + COMPETITION_WEIGHT == 100

    def test_pricing_constants_positive(self):
        """All pricing constants must be positive."""
        assert ESTIMATED_SHIPPING_COST_USD > 0
        assert ESTIMATED_CPA_USD > 0
        assert TARGET_PROFIT_USD > 0

    def test_competition_thresholds_ordered(self):
        """LOW max sellers must be less than HIGH min sellers."""
        assert COMPETITION_LOW_MAX_SELLERS < COMPETITION_HIGH_MIN_SELLERS

    def test_competition_level_medium_value(self):
        """CompetitionLevel.MEDIUM must serialize as 'MEDIUM' (not 'MED')."""
        assert CompetitionLevel.MEDIUM.value == "MEDIUM"


class TestCompetitionLevelBackwardCompat:
    """Ensure legacy 'MED' value is accepted for backward compatibility."""

    def test_legacy_med_accepted_in_product_score(self):
        """ProductScore should accept 'MED' and normalize to MEDIUM."""
        score = ProductScore(
            product_id="LEGACY-001",
            margin_pct=50.0,
            competition_level="MED",
            trend_score=0.5,
            total_score=55.0,
            recommendation=ProductRecommendation.WATCH,
            reasoning="Legacy backward compatibility test with MED value",
        )
        assert score.competition_level == CompetitionLevel.MEDIUM
        assert score.competition_level.value == "MEDIUM"

    def test_medium_value_accepted_in_product_score(self):
        """ProductScore should accept the canonical 'MEDIUM' value."""
        score = ProductScore(
            product_id="NEW-001",
            margin_pct=50.0,
            competition_level="MEDIUM",
            trend_score=0.5,
            total_score=55.0,
            recommendation=ProductRecommendation.WATCH,
            reasoning="New canonical MEDIUM value test for score",
        )
        assert score.competition_level == CompetitionLevel.MEDIUM
