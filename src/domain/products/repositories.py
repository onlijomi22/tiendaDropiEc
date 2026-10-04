"""Product repository interface (Dependency Inversion Principle).

Defines the contract for all product data sources. Infrastructure layer
must implement this interface. Use cases depend ONLY on this interface,
never on concrete implementations.

Spec: specs/products/product.spec.md#ca-prod-04
"""

from abc import ABC, abstractmethod
from src.domain.products.entities import Product, ProductScore


class IProductRepository(ABC):
    """Abstract repository for Dropi product data.

    Implementations:
        - DropiProductRepository (infrastructure/dropi/)
        - MockProductRepository (tests/)
    """

    @abstractmethod
    async def get_catalog(self, category: str, limit: int = 50) -> list[Product]:
        """Fetch products from Dropi catalog for a given category.

        Args:
            category: Dropi product category name.
            limit: Maximum number of products to return (default 50, spec max).

        Returns:
            List of Product entities from Dropi.

        Raises:
            DropiAuthError: If Dropi session is invalid.
            DropiScrapingError: If Dropi UI structure has changed.
        """

    @abstractmethod
    async def get_product(self, product_id: str) -> Product:
        """Fetch a single product by ID.

        Args:
            product_id: Unique product identifier in Dropi.

        Returns:
            Product entity.

        Raises:
            ProductNotFoundError: If product does not exist.
            DropiScrapingError: If scraping fails.
        """

    @abstractmethod
    async def save_score(self, score: ProductScore) -> None:
        """Persist an AI-generated ProductScore for later reference.

        Args:
            score: The ProductScore to persist.
        """

    @abstractmethod
    async def get_scored_products(
        self, recommendation: str | None = None
    ) -> list[ProductScore]:
        """Retrieve previously scored products, optionally filtered by recommendation.

        Args:
            recommendation: Optional filter: 'BUY', 'SKIP', or 'WATCH'.

        Returns:
            List of ProductScore entities.
        """
