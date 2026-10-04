"""Unit tests for ResearchMarketUseCase."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.application.intelligence.research_market import (
    ResearchMarketInput,
    ResearchMarketUseCase,
)
from src.domain.intelligence.entities import CompetitorListing
from src.domain.products.entities import CompetitionLevel, Product


def _make_product() -> Product:
    return Product(
        id="TEST-001",
        name="Licuadora Portatil USB",
        category="cocina",
        dropi_price=12.00,
        suggested_price=30.00,
        stock=50,
        supplier_id="SUP-001",
        images=["https://img.test/1.jpg"],
        description="Licuadora portatil recargable USB",
    )


def _make_competitors(count: int) -> list[CompetitorListing]:
    return [
        CompetitorListing(
            title=f"Competitor {i}",
            price_usd=25.0 + i,
            url=f"https://ml.com/{i}",
        )
        for i in range(count)
    ]


class TestResearchMarketUseCase:

    @pytest.mark.asyncio
    async def test_low_competition(self):
        """Fewer than 5 competitors should yield LOW competition."""
        ml_scraper = AsyncMock()
        ml_scraper.search_competitors.return_value = _make_competitors(3)
        gemini_search = AsyncMock()
        gemini_search.research_product_category.return_value = {
            "buyer_concerns": ["durability"],
            "buyer_positives": ["portable"],
            "sources_used": ["https://source.com"],
        }

        uc = ResearchMarketUseCase(ml_scraper=ml_scraper, gemini_search=gemini_search)
        result = await uc.execute(ResearchMarketInput(product=_make_product()))

        assert result.competition_level == CompetitionLevel.LOW
        assert result.competition_count == 3
        assert len(result.buyer_concerns) == 1

    @pytest.mark.asyncio
    async def test_medium_competition(self):
        """5-20 competitors should yield MEDIUM competition."""
        ml_scraper = AsyncMock()
        ml_scraper.search_competitors.return_value = _make_competitors(10)
        gemini_search = AsyncMock()
        gemini_search.research_product_category.return_value = {}

        uc = ResearchMarketUseCase(ml_scraper=ml_scraper, gemini_search=gemini_search)
        result = await uc.execute(ResearchMarketInput(product=_make_product()))

        assert result.competition_level == CompetitionLevel.MEDIUM
        assert result.competition_count == 10

    @pytest.mark.asyncio
    async def test_high_competition(self):
        """More than 20 competitors should yield HIGH competition."""
        ml_scraper = AsyncMock()
        ml_scraper.search_competitors.return_value = _make_competitors(25)
        gemini_search = AsyncMock()
        gemini_search.research_product_category.return_value = {}

        uc = ResearchMarketUseCase(ml_scraper=ml_scraper, gemini_search=gemini_search)
        result = await uc.execute(ResearchMarketInput(product=_make_product()))

        assert result.competition_level == CompetitionLevel.HIGH

    @pytest.mark.asyncio
    async def test_avg_competitor_price(self):
        """Average price should be computed from competitor listings."""
        ml_scraper = AsyncMock()
        ml_scraper.search_competitors.return_value = [
            CompetitorListing(title="A", price_usd=20.0, url="https://a.com"),
            CompetitorListing(title="B", price_usd=30.0, url="https://b.com"),
        ]
        gemini_search = AsyncMock()
        gemini_search.research_product_category.return_value = {}

        uc = ResearchMarketUseCase(ml_scraper=ml_scraper, gemini_search=gemini_search)
        result = await uc.execute(ResearchMarketInput(product=_make_product()))

        assert result.avg_competitor_price == 25.0
