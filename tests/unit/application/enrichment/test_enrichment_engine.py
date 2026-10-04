"""Tests for EnrichmentEngine — building EnrichedProduct from evidence."""

import pytest
from datetime import datetime
from src.application.enrichment.enrichment_engine import EnrichmentEngine
from src.domain.enrichment.entities import (
    DataOrigin, DataType, MatchQuality,
    ProductEvidence, ProductImage,
)
from src.domain.products.entities import CompetitionLevel, Product


def _product(dropi_price: float = 5.0, suggested_price: float = 35.0) -> Product:
    return Product(
        id="ENG-001", name="POLVO DESTAPA CANERIAS GBJ061", category="hogar",
        dropi_price=dropi_price, suggested_price=suggested_price, stock=100,
        supplier_id="S1", supplier_name="TestSupplier",
        images=["https://d39ru7awumhhs2.cloudfront.net/products/test.jpg"],
        description="Polvo destapador 500g para tuberias de PVC",
    )


def _fact(field: str, value, origin=DataOrigin.DROPI, conf=1.0, **kw) -> ProductEvidence:
    return ProductEvidence(
        field=field, value=value, data_type=DataType.FACT,
        origin=origin, confidence=conf, collected_at=datetime.utcnow(), **kw,
    )


def _clean_image() -> ProductImage:
    return ProductImage(
        url="https://d39ru7awumhhs2.cloudfront.net/products/test.jpg",
        origin=DataOrigin.DROPI, is_clean=True, is_product_only=True,
    )


class TestEnrichmentEngine:

    def setup_method(self):
        self.engine = EnrichmentEngine()

    def test_basic_enrichment(self):
        """Should build an EnrichedProduct from minimal evidence."""
        product = _product()
        evidences = [_fact("name", "Polvo Destapa"), _fact("dropi_price", 5.0)]
        images = [_clean_image(), _clean_image()]

        result = self.engine.build(product, evidences, images)

        assert result.product_id == "ENG-001"
        assert result.dropi_price == 5.0
        assert result.sale_price == 35.0
        assert result.evidence_count == 2
        assert result.category_config is not None
        assert result.category_config.slug == "hogar"

    def test_display_name_cleaned(self):
        """Product codes like GBJ061 should be removed from display name."""
        product = _product()
        result = self.engine.build(product, [_fact("name", "test")], [_clean_image()])
        assert "GBJ061" not in result.display_name

    def test_competitor_avg_excludes_category_only(self):
        """CATEGORY_ONLY matches should not affect competitor avg price."""
        product = _product()
        evidences = [
            _fact("competitor_price", 30.0, DataOrigin.MERCADOLIBRE, 0.95,
                  match_quality=MatchQuality.EXACT, source_url="https://ml.com/1"),
            _fact("competitor_price", 100.0, DataOrigin.MERCADOLIBRE, 0.5,
                  match_quality=MatchQuality.CATEGORY_ONLY, source_url="https://ml.com/2"),
        ]

        result = self.engine.build(product, evidences, [_clean_image()])

        # Only the EXACT match should count
        assert result.competitor_avg_price == 30.0

    def test_reviews_gated_by_confidence(self):
        """Reviews below 0.7 confidence should not be displayable."""
        product = _product()
        evidences = [
            ProductEvidence(
                field="real_review", value="Good product", data_type=DataType.FACT,
                origin=DataOrigin.GOOGLE_SEARCH, confidence=0.7,
                collected_at=datetime.utcnow(),
            ),
            ProductEvidence(
                field="real_review", value="Meh product", data_type=DataType.FACT,
                origin=DataOrigin.GOOGLE_SEARCH, confidence=0.4,
                collected_at=datetime.utcnow(),
            ),
        ]

        result = self.engine.build(product, evidences, [_clean_image()])

        assert len(result.real_reviews) == 1  # Only the 0.7 one passes gate
        assert result.real_reviews[0].text == "Good product"
        assert len(result.displayable_reviews) == 1

    def test_insufficient_images_noted(self):
        """Missing clean images should generate a review note."""
        product = _product()
        dirty_image = ProductImage(
            url="https://example.com/dirty.jpg",
            origin=DataOrigin.DROPI, is_clean=False, is_product_only=False,
        )

        result = self.engine.build(product, [], [dirty_image])

        assert any("IMAGENES" in note for note in result.human_review_notes)

    def test_viability_high_margin_low_competition(self):
        """High margin + low competition should be viable."""
        product = _product(dropi_price=5.0, suggested_price=35.0)
        result = self.engine.build(product, [], [_clean_image()])
        assert result.viable is True
        assert result.margin_pct > 35.0

    def test_specs_extracted_from_description(self):
        """Product specs should be extracted from description text."""
        product = Product(
            id="SPEC-001", name="Licuadora 500ml",
            category="cocina", dropi_price=10.0, suggested_price=30.0,
            stock=50, supplier_id="S1",
            images=["https://d39ru7awumhhs2.cloudfront.net/test.jpg"],
            description="Licuadora portatil de 500ml con motor de 150w y peso 0.8kg",
        )
        result = self.engine.build(product, [], [_clean_image()])
        spec_names = {s.name for s in result.specifications}
        assert "Volumen" in spec_names
        assert "Potencia" in spec_names
        assert "Peso" in spec_names

    def test_slug_generation(self):
        """Slug should be URL-safe."""
        product = _product()
        product = product.model_copy(update={"name": "Sartén Antiadherente 28cm"})
        result = self.engine.build(product, [], [_clean_image()])
        assert result.slug == "sarten-antiadherente-28cm"
        assert " " not in result.slug

    def test_pricing_warning_when_competitors_cheaper(self):
        """Should warn when competitor avg is significantly below sale price."""
        product = _product(suggested_price=35.0)
        evidences = [
            _fact("competitor_price", 10.0, DataOrigin.MERCADOLIBRE, 0.9,
                  match_quality=MatchQuality.EXACT, source_url="https://ml.com/1"),
        ]

        result = self.engine.build(product, evidences, [_clean_image()])

        assert any("PRICING" in note for note in result.human_review_notes)
