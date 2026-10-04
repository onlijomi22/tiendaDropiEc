"""Shared pytest fixtures for TiendaDropiEc tests.

Provides mock implementations of repository interfaces,
enabling unit tests without real Dropi/API connections.
"""

import pytest
from unittest.mock import AsyncMock
from src.domain.products.entities import (
    Product, ProductScore, ProductRecommendation, CompetitionLevel
)
from src.domain.products.repositories import IProductRepository


@pytest.fixture
def sample_product() -> Product:
    """A valid Dropi product with good margins for testing."""
    return Product(
        id="PROD-001",
        name="Aspiradora Inalámbrica Portail",
        category="hogar",
        dropi_price=18.00,
        suggested_price=35.00,
        stock=25,
        supplier_id="SUP-001",
        images=["https://dropi.ec/img/prod001.jpg"],
        description="Aspiradora portátil sin cable, ideal para carro y hogar",
        weight_kg=0.8,
        tags=["hogar", "limpieza", "electro"],
    )


@pytest.fixture
def low_margin_product() -> Product:
    """A product with insufficient margin (< 25%)."""
    return Product(
        id="PROD-002",
        name="Cable USB Genérico",
        category="electrónica",
        dropi_price=8.00,
        suggested_price=9.50,
        stock=100,
        supplier_id="SUP-002",
        images=["https://dropi.ec/img/prod002.jpg"],
        description="Cable USB tipo C",
    )


@pytest.fixture
def low_stock_product() -> Product:
    """A product with good margin but insufficient stock."""
    return Product(
        id="PROD-003",
        name="Reloj Inteligente Premium",
        category="electrónica",
        dropi_price=20.00,
        suggested_price=55.00,
        stock=3,  # Below minimum of 10
        supplier_id="SUP-003",
        images=["https://dropi.ec/img/prod003.jpg"],
        description="Smartwatch con monitor de salud",
    )


@pytest.fixture
def mock_product_repo(sample_product, low_stock_product):
    """AsyncMock implementing IProductRepository for unit tests."""
    repo = AsyncMock(spec=IProductRepository)
    repo.get_product.return_value = sample_product
    repo.get_catalog.return_value = [sample_product, low_stock_product]
    repo.save_score.return_value = None
    repo.get_scored_products.return_value = []
    return repo
