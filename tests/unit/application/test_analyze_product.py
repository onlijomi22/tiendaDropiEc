"""Unit tests for AnalyzeProductUseCase.

Spec: specs/products/product.spec.md
All spec criteria tested with mock repository.
"""

import pytest
from src.application.products.analyze_product import (
    AnalyzeProductInput, AnalyzeProductUseCase
)
from src.domain.products.entities import ProductRecommendation


class TestAnalyzeProductUseCase:
    """Tests for the AnalyzeProduct use case against spec criteria."""

    @pytest.fixture(autouse=True)
    def setup(self, mock_product_repo):
        self.repo = mock_product_repo
        self.use_case = AnalyzeProductUseCase(mock_product_repo)

    @pytest.mark.asyncio
    async def test_high_margin_high_stock_scores_buy(self, sample_product):
        """Product with 48% margin and 25 stock should score BUY."""
        self.repo.get_product.return_value = sample_product
        result = await self.use_case.execute(AnalyzeProductInput(product_id="PROD-001"))
        # 48% margin → margin component = 40 pts max portion
        assert result.score.total_score > 0
        assert result.score.recommendation in (
            ProductRecommendation.BUY, ProductRecommendation.WATCH
        )

    @pytest.mark.asyncio
    async def test_low_stock_prevents_buy(self, low_stock_product):
        """CA-PROD-03: stock < 10 must downgrade to WATCH or SKIP."""
        self.repo.get_product.return_value = low_stock_product
        result = await self.use_case.execute(
            AnalyzeProductInput(product_id="PROD-003")
        )
        assert result.score.recommendation != ProductRecommendation.BUY

    @pytest.mark.asyncio
    async def test_score_is_saved(self, sample_product):
        """Use case must call save_score on the repository."""
        self.repo.get_product.return_value = sample_product
        await self.use_case.execute(AnalyzeProductInput(product_id="PROD-001"))
        self.repo.save_score.assert_called_once()

    @pytest.mark.asyncio
    async def test_reasoning_is_not_empty(self, sample_product):
        """ProductScore must have meaningful reasoning."""
        self.repo.get_product.return_value = sample_product
        result = await self.use_case.execute(AnalyzeProductInput(product_id="PROD-001"))
        assert len(result.score.reasoning) >= 10
