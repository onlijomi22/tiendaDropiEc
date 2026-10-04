"""Use case: Find winning products from a Dropi category.

Spec: specs/products/product.spec.md
Orchestrates AnalyzeProductUseCase across a full category.
"""

from dataclasses import dataclass, field
from src.application.products.analyze_product import (
    AnalyzeProductInput, AnalyzeProductOutput, AnalyzeProductUseCase
)
from src.domain.products.entities import ProductRecommendation
from src.domain.products.repositories import IProductRepository
from src.shared.logger import logger

_MAX_PRODUCTS_PER_RUN = 50  # Spec constraint


@dataclass
class FindWinnersInput:
    """Input DTO for the FindWinners use case."""
    category: str
    limit: int = _MAX_PRODUCTS_PER_RUN


@dataclass
class FindWinnersOutput:
    """Output DTO: products scored as BUY, WATCH, SKIP."""
    buy: list[AnalyzeProductOutput] = field(default_factory=list)
    watch: list[AnalyzeProductOutput] = field(default_factory=list)
    skip: list[AnalyzeProductOutput] = field(default_factory=list)

    @property
    def total_analyzed(self) -> int:
        """Total number of products analyzed."""
        return len(self.buy) + len(self.watch) + len(self.skip)


class FindWinnersUseCase:
    """Scan a Dropi category and identify the best products to sell.

    Args:
        product_repo: Repository for product data access.
    """

    def __init__(self, product_repo: IProductRepository) -> None:
        self._repo = product_repo
        self._analyze_uc = AnalyzeProductUseCase(product_repo)

    async def execute(self, input_data: FindWinnersInput) -> FindWinnersOutput:
        """Scan category and score all products.

        Args:
            input_data: Category and limit configuration.

        Returns:
            FindWinnersOutput with products grouped by recommendation.
        """
        limit = min(input_data.limit, _MAX_PRODUCTS_PER_RUN)
        products = await self._repo.get_catalog(input_data.category, limit=limit)
        logger.info(f"Scanning {len(products)} products in '{input_data.category}'")

        output = FindWinnersOutput()
        for product in products:
            try:
                result = await self._analyze_uc.execute(
                    AnalyzeProductInput(product_id=product.id)
                )
                if result.score.recommendation == ProductRecommendation.BUY:
                    output.buy.append(result)
                elif result.score.recommendation == ProductRecommendation.WATCH:
                    output.watch.append(result)
                else:
                    output.skip.append(result)
            except Exception as e:
                logger.warning(f"Failed to analyze product {product.id}: {e}")
                continue

        logger.info(
            f"FindWinners complete: {len(output.buy)} BUY, "
            f"{len(output.watch)} WATCH, {len(output.skip)} SKIP"
        )
        return output
