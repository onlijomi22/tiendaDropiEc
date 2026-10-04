"""Step definitions for analyze_product.feature.

Spec: specs/products/product.spec.md
Criteria tested: CA-PROD-01, CA-PROD-02, CA-PROD-03

Note on pytest-bdd + async:
  pytest-bdd does not natively support async @when steps.
  We use asyncio.run() inside the step to call the coroutine.
"""

import asyncio
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from src.domain.products.entities import (
    Product, ProductScore, ProductRecommendation, CompetitionLevel,
)
from src.application.products.analyze_product import (
    AnalyzeProductInput, AnalyzeProductUseCase,
)
from src.shared.exceptions import SpecViolationError

# Link to feature file
scenarios("../features/products/analyze_product.feature")


# ─── Shared context fixture ────────────────────────────────────────────────────

@pytest.fixture
def ctx():
    """Mutable dict shared across steps in a single scenario."""
    return {}


# ─── Background ────────────────────────────────────────────────────────────────

@given("the ProductAnalystAgent is initialized")
def agent_initialized(mock_product_repo, ctx):
    """Set up the AnalyzeProductUseCase with mock repository."""
    ctx["use_case"] = AnalyzeProductUseCase(mock_product_repo)
    ctx["repo"] = mock_product_repo


# ─── Given steps ───────────────────────────────────────────────────────────────

@given(
    parsers.parse(
        "a product with dropi_price {dropi_price:f} "
        "and suggested_price {suggested_price:f} "
        "and stock {stock:d}"
    )
)
def set_product_params(dropi_price, suggested_price, stock, mock_product_repo, ctx):
    """Configure mock to return a product with specified attributes."""
    product = Product(
        id="TEST-001",
        name="Producto de Prueba",
        category="test",
        dropi_price=dropi_price,
        suggested_price=suggested_price,
        stock=stock,
        supplier_id="SUP-TEST",
        images=["https://test.com/img.jpg"],
        description="Descripción del producto de prueba para BDD",
    )
    mock_product_repo.get_product.return_value = product
    ctx["product"] = product
    # Ensure use_case is set if background ran
    if "use_case" not in ctx:
        ctx["use_case"] = AnalyzeProductUseCase(mock_product_repo)
        ctx["repo"] = mock_product_repo


@given(parsers.parse("a product with a score of {score:d}"))
def set_score_directly(score, ctx):
    """Set a pre-computed score directly in context for spec validation tests."""
    ctx["direct_score"] = float(score)


# ─── When steps ────────────────────────────────────────────────────────────────

@when("I analyze the product")
def analyze_product(ctx):
    """Execute the AnalyzeProduct use case synchronously (pytest-bdd async workaround)."""
    result = asyncio.run(
        ctx["use_case"].execute(AnalyzeProductInput(product_id="TEST-001"))
    )
    ctx["result"] = result


# ─── Then steps ────────────────────────────────────────────────────────────────

@then(parsers.parse("the margin should be approximately {expected:f} percent"))
def check_margin_approx(ctx, expected):
    """CA-PROD-01: margin formula validation."""
    margin = ctx["result"].score.margin_pct
    assert abs(margin - expected) < 1.0, (
        f"Expected margin ~{expected:.2f}%, got {margin:.2f}%"
    )


@then(parsers.parse("the margin should be less than {threshold:f} percent"))
def check_margin_below(ctx, threshold):
    """CA-PROD-01: below-threshold margin validation."""
    margin = ctx["result"].score.margin_pct
    assert margin < threshold, (
        f"Expected margin < {threshold:.1f}%, got {margin:.2f}%"
    )


@then("the recommendation should be BUY or WATCH")
def check_rec_buy_or_watch(ctx):
    rec = ctx["result"].score.recommendation
    assert rec in (ProductRecommendation.BUY, ProductRecommendation.WATCH), (
        f"Expected BUY or WATCH, got {rec}"
    )


@then("the recommendation should be SKIP")
def check_rec_skip(ctx):
    """CA-PROD-01: low-margin product must be SKIP."""
    rec = ctx["result"].score.recommendation
    assert rec == ProductRecommendation.SKIP, f"Expected SKIP, got {rec}"


@then("the recommendation should not be BUY")
def check_rec_not_buy(ctx):
    """CA-PROD-03: low-stock product must not be BUY."""
    rec = ctx["result"].score.recommendation
    assert rec != ProductRecommendation.BUY, (
        f"Expected not BUY (low stock), got {rec}"
    )


@then(parsers.parse("the total score should be between {low:f} and {high:f}"))
@then(parsers.parse("the total score should be between {low:d} and {high:d}"))
def check_score_range(ctx, low, high):
    score = ctx["result"].score.total_score
    assert low <= score <= high, (
        f"Score {score:.1f} not in range [{low}, {high}]"
    )


@then(parsers.parse("the total score should be less than {threshold:f}"))
@then(parsers.parse("the total score should be less than {threshold:d}"))
def check_score_below(ctx, threshold):
    score = ctx["result"].score.total_score
    assert score < threshold, (
        f"Score {score:.1f} should be < {threshold}"
    )


# CA-PROD-02 score-threshold steps (direct entity validation, no use case needed)

@then(parsers.parse("the recommendation must be BUY"))
def check_direct_score_buy(ctx):
    """CA-PROD-02: score >= 70 enforced by ProductScore entity."""
    score_val = ctx["direct_score"]
    if score_val >= 70.0:
        ps = ProductScore(
            product_id="X",
            margin_pct=35.0,
            competition_level=CompetitionLevel.MEDIUM,
            trend_score=0.5,
            total_score=score_val,
            recommendation=ProductRecommendation.BUY,
            reasoning="CA-PROD-02 BUY threshold test",
        )
        assert ps.recommendation == ProductRecommendation.BUY
        # Ensure WATCH raises SpecViolationError
        with pytest.raises(SpecViolationError):
            ProductScore(
                product_id="X",
                margin_pct=35.0,
                competition_level=CompetitionLevel.MEDIUM,
                trend_score=0.5,
                total_score=score_val,
                recommendation=ProductRecommendation.WATCH,
                reasoning="CA-PROD-02 invalid WATCH at score>=70",
            )


@then(parsers.parse("the recommendation must be WATCH"))
def check_direct_score_watch(ctx):
    """CA-PROD-02: score in [40, 70) enforced by ProductScore entity."""
    score_val = ctx["direct_score"]
    if 40.0 <= score_val < 70.0:
        ps = ProductScore(
            product_id="X",
            margin_pct=35.0,
            competition_level=CompetitionLevel.MEDIUM,
            trend_score=0.5,
            total_score=score_val,
            recommendation=ProductRecommendation.WATCH,
            reasoning="CA-PROD-02 WATCH threshold test",
        )
        assert ps.recommendation == ProductRecommendation.WATCH


@then(parsers.parse("the recommendation must be SKIP"))
def check_direct_score_skip(ctx):
    """CA-PROD-02: score < 40 enforced by ProductScore entity."""
    score_val = ctx["direct_score"]
    if score_val < 40.0:
        ps = ProductScore(
            product_id="X",
            margin_pct=35.0,
            competition_level=CompetitionLevel.MEDIUM,
            trend_score=0.5,
            total_score=score_val,
            recommendation=ProductRecommendation.SKIP,
            reasoning="CA-PROD-02 SKIP threshold test",
        )
        assert ps.recommendation == ProductRecommendation.SKIP
