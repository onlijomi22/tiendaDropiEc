"""Unit tests for Product domain entities.

Spec: specs/products/product.spec.md
Tests CA-PROD-01, CA-PROD-02, CA-PROD-03 at the entity level.
"""

import pytest
from pydantic import ValidationError
from src.domain.products.entities import (
    Product, ProductScore, ProductRecommendation, CompetitionLevel
)
from src.shared.exceptions import SpecViolationError


class TestProductMargin:
    """Tests for CA-PROD-01: margin calculation."""

    def test_margin_calculation_correct(self):
        """CA-PROD-01: margin = (selling - cost) / selling * 100."""
        product = Product(
            id="P1", name="Test", category="hogar",
            dropi_price=18.0, suggested_price=35.0, stock=20,
            supplier_id="S1", images=["http://img.com/1.jpg"],
            description="Test product"
        )
        expected_margin = (35.0 - 18.0) / 35.0 * 100
        assert abs(product.margin_pct - expected_margin) < 0.01

    def test_suggested_price_must_exceed_dropi_price(self):
        """Product validation: selling price must be above cost."""
        with pytest.raises(ValidationError):
            Product(
                id="P2", name="Test", category="hogar",
                dropi_price=20.0, suggested_price=20.0,  # Equal, not greater
                stock=10, supplier_id="S1",
                images=["http://img.com/1.jpg"], description="Test"
            )


class TestProductScore:
    """Tests for CA-PROD-02: score thresholds and recommendations."""

    def _make_score(
        self,
        total_score: float,
        recommendation: ProductRecommendation
    ) -> ProductScore:
        return ProductScore(
            product_id="P1",
            margin_pct=35.0,
            competition_level=CompetitionLevel.MEDIUM,
            trend_score=0.5,
            total_score=total_score,
            recommendation=recommendation,
            reasoning="Test reasoning for this product score",
        )

    def test_score_70_requires_buy(self):
        """CA-PROD-02: score >= 70 must be BUY."""
        score = self._make_score(70.0, ProductRecommendation.BUY)
        assert score.recommendation == ProductRecommendation.BUY

    def test_score_70_cannot_be_watch(self):
        """CA-PROD-02: score >= 70 cannot be WATCH (SpecViolationError)."""
        with pytest.raises(SpecViolationError) as exc_info:
            self._make_score(70.0, ProductRecommendation.WATCH)
        assert "CA-PROD-02" in str(exc_info.value)

    def test_score_55_requires_watch(self):
        """CA-PROD-02: score in [40, 70) must be WATCH."""
        score = self._make_score(55.0, ProductRecommendation.WATCH)
        assert score.recommendation == ProductRecommendation.WATCH

    def test_score_30_requires_skip(self):
        """CA-PROD-02: score < 40 must be SKIP."""
        score = self._make_score(30.0, ProductRecommendation.SKIP)
        assert score.recommendation == ProductRecommendation.SKIP

    def test_total_score_must_be_0_to_100(self):
        """Score must be between 0 and 100."""
        with pytest.raises(ValidationError):
            ProductScore(
                product_id="P1", margin_pct=30.0,
                competition_level=CompetitionLevel.LOW,
                trend_score=0.5, total_score=150.0,  # Invalid
                recommendation=ProductRecommendation.BUY,
                reasoning="Invalid score test"
            )
