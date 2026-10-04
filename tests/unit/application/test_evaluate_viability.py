"""Unit tests for EvaluateViabilityUseCase."""

import pytest
from src.application.intelligence.evaluate_viability import EvaluateViabilityUseCase
from src.domain.business_rules import (
    TARGET_MARGIN_PCT,
    ESTIMATED_CPA_USD,
    ESTIMATED_SHIPPING_COST_USD,
    TARGET_PROFIT_USD,
)
from src.domain.intelligence.entities import MarketInsight, ProductCopyDraft
from src.domain.products.entities import CompetitionLevel, Product


def _make_product(dropi_price: float = 12.0) -> Product:
    return Product(
        id="TEST-V01",
        name="Test Product",
        category="cocina",
        dropi_price=dropi_price,
        suggested_price=35.0,
        stock=50,
        supplier_id="SUP-001",
        images=["https://img.test/1.jpg"],
        description="Test product for viability",
    )


def _make_insight(competition: CompetitionLevel = CompetitionLevel.LOW) -> MarketInsight:
    return MarketInsight(
        category="cocina",
        product_name="Test Product",
        competition_level=competition,
        competition_count=3,
        avg_competitor_price=30.0,
    )


def _make_copy(
    suggested_price: float = 35.0,
    is_bulky: bool = False,
) -> ProductCopyDraft:
    return ProductCopyDraft(
        product_id="TEST-V01",
        product_name="Test Product",
        landing_headline="Test headline for product",
        landing_subheadline="Test subheadline for product landing",
        benefits=["benefit 1", "benefit 2"],
        review_quotes=["Great product review quote"],
        objection_handlers=["objection response 1"],
        tiktok_hook="Hook for tiktok video",
        tiktok_script="Full tiktok script text",
        meta_headline="Meta headline text",
        meta_body="Meta body text for the ad campaign",
        is_bulky=is_bulky,
        suggested_price_usd=suggested_price,
        suggested_margin_pct=50.0,
        data_sources=["https://source.com"],
        human_review_notes="Verify pricing",
    )


class TestEvaluateViabilityUseCase:

    def setup_method(self):
        self.uc = EvaluateViabilityUseCase()

    def test_viable_product(self):
        """High margin + low competition should be viable."""
        product = _make_product(dropi_price=12.0)
        viable, reason, _ = self.uc.execute(
            product=product,
            sale_price=35.0,
            market_insight=_make_insight(CompetitionLevel.LOW),
            copy_draft=_make_copy(),
        )
        margin = (35.0 - 12.0) / 35.0 * 100
        assert margin >= TARGET_MARGIN_PCT
        assert viable is True

    def test_not_viable_low_margin(self):
        """Margin below TARGET_MARGIN_PCT should not be viable."""
        product = _make_product(dropi_price=25.0)
        viable, reason, _ = self.uc.execute(
            product=product,
            sale_price=35.0,
            market_insight=_make_insight(CompetitionLevel.LOW),
            copy_draft=_make_copy(),
        )
        margin = (35.0 - 25.0) / 35.0 * 100  # ~28.6%
        assert margin < TARGET_MARGIN_PCT
        assert viable is False

    def test_not_viable_high_competition(self):
        """HIGH competition should not be viable even with good margin."""
        product = _make_product(dropi_price=12.0)
        viable, reason, _ = self.uc.execute(
            product=product,
            sale_price=35.0,
            market_insight=_make_insight(CompetitionLevel.HIGH),
            copy_draft=_make_copy(),
        )
        assert viable is False
        assert "competencia" in reason.lower()

    def test_bulky_not_viable(self):
        """Bulky products should not be viable."""
        product = _make_product(dropi_price=12.0)
        viable, reason, _ = self.uc.execute(
            product=product,
            sale_price=35.0,
            market_insight=_make_insight(CompetitionLevel.LOW),
            copy_draft=_make_copy(is_bulky=True),
        )
        assert viable is False
        assert "volumen" in reason.lower()

    def test_pricing_review_flag(self):
        """AI price below minimum viable should add review note."""
        product = _make_product(dropi_price=12.0)
        min_viable = 12.0 + ESTIMATED_SHIPPING_COST_USD + ESTIMATED_CPA_USD + TARGET_PROFIT_USD
        low_ai_price = min_viable - 5.0

        _, _, updated_copy = self.uc.execute(
            product=product,
            sale_price=35.0,
            market_insight=_make_insight(CompetitionLevel.LOW),
            copy_draft=_make_copy(suggested_price=low_ai_price),
        )
        assert "PRICING REVIEW" in updated_copy.human_review_notes

    def test_no_pricing_flag_when_price_ok(self):
        """AI price above minimum viable should not add review note."""
        product = _make_product(dropi_price=12.0)
        min_viable = 12.0 + ESTIMATED_SHIPPING_COST_USD + ESTIMATED_CPA_USD + TARGET_PROFIT_USD

        _, _, updated_copy = self.uc.execute(
            product=product,
            sale_price=35.0,
            market_insight=_make_insight(CompetitionLevel.LOW),
            copy_draft=_make_copy(suggested_price=min_viable + 5.0),
        )
        assert "PRICING REVIEW" not in updated_copy.human_review_notes
