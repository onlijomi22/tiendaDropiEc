"""Tests for ProductMatcher — matching Dropi products to external listings."""

import pytest
from src.application.enrichment.product_matcher import ProductMatcher
from src.domain.enrichment.entities import MatchQuality
from src.domain.intelligence.entities import CompetitorListing
from src.domain.products.entities import Product


def _product(name: str = "Polvo Destapa Canerias 500g", price: float = 16.0) -> Product:
    return Product(
        id="T1", name=name, category="hogar",
        dropi_price=5.0, suggested_price=price, stock=50,
        supplier_id="S1", images=["https://img.test/1.jpg"],
        description=f"Producto de prueba: {name}",
    )


def _listing(title: str, price: float = 15.0) -> CompetitorListing:
    return CompetitorListing(title=title, price_usd=price, url="https://ml.com/1")


class TestProductMatcher:

    def setup_method(self):
        self.matcher = ProductMatcher()

    def test_exact_match_same_name(self):
        """Nearly identical names should yield EXACT."""
        result = self.matcher.match(
            _product("Polvo Destapa Canerias 500g"),
            _listing("Polvo Destapa Canerias 500g", price=14.0),
        )
        assert result.quality == MatchQuality.EXACT
        assert result.match_score >= 0.7

    def test_similar_match_related_product(self):
        """Related product with shared key words should yield SIMILAR."""
        result = self.matcher.match(
            _product("Polvo Destapa Canerias 500g"),
            _listing("Polvo Destapa Canerias Tuberias 500g"),
        )
        assert result.quality in (MatchQuality.EXACT, MatchQuality.SIMILAR)
        assert result.match_score >= 0.4

    def test_different_variant_is_category_only(self):
        """Different product variant (polvo vs destapador) is CATEGORY_ONLY."""
        result = self.matcher.match(
            _product("Polvo Destapa Canerias 500g"),
            _listing("Destapador Canerias Tuberias Liquido"),
        )
        assert result.quality == MatchQuality.CATEGORY_ONLY

    def test_category_only_different_product(self):
        """Completely different product should yield CATEGORY_ONLY."""
        result = self.matcher.match(
            _product("Polvo Destapa Canerias 500g"),
            _listing("Sarten Antiadherente 28cm", price=25.0),
        )
        assert result.quality == MatchQuality.CATEGORY_ONLY
        assert result.match_score < 0.4

    def test_numeric_specs_bonus(self):
        """Shared measurements like '500g' should increase match score."""
        with_nums = self.matcher.match(
            _product("Licuadora Portatil USB 500ml"),
            _listing("Licuadora Portatil 500ml"),
        )
        without_nums = self.matcher.match(
            _product("Licuadora Portatil USB 500ml"),
            _listing("Licuadora Portatil 350ml"),
        )
        assert with_nums.match_score > without_nums.match_score

    def test_price_incompatibility_penalizes(self):
        """Huge price difference suggests different products."""
        result = self.matcher.match(
            _product("Aspiradora Inalambrica", price=35.0),
            _listing("Aspiradora Industrial Profesional", price=350.0),
        )
        assert result.price_compatible is False

    def test_match_result_has_reasoning(self):
        """Match result should explain why it decided."""
        result = self.matcher.match(
            _product("Termo Acero 500ml"),
            _listing("Termo Acero Inoxidable 500ml"),
        )
        assert "name_sim" in result.reasoning
        assert "price" in result.reasoning
