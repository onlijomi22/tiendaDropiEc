"""Tests for EvidenceCollector — gathering evidence from multiple sources."""

import pytest
from src.application.enrichment.evidence_collector import EvidenceCollector
from src.domain.enrichment.entities import DataOrigin, DataType
from src.domain.intelligence.entities import CompetitorListing
from src.domain.products.entities import Product


def _product() -> Product:
    return Product(
        id="EC-001", name="Polvo Destapa Canerias 500g", category="hogar",
        dropi_price=5.0, suggested_price=16.0, stock=100,
        supplier_id="S1", supplier_name="TestSupplier",
        images=["https://d39ru7awumhhs2.cloudfront.net/products/test.jpg"],
        description="Polvo destapador de tuberias 500g. Seguro para PVC.",
        weight_kg=0.5,
    )


class TestCollectFromDropi:

    def setup_method(self):
        self.collector = EvidenceCollector()

    def test_all_facts_collected(self):
        """Should extract all core fields as FACT with confidence 1.0."""
        evidences = self.collector.collect_from_dropi(_product())
        facts = [e for e in evidences if e.data_type == DataType.FACT]
        assert len(facts) >= 8  # name, category, prices, stock, supplier, desc, image
        assert all(e.confidence == 1.0 for e in facts)
        assert all(e.origin == DataOrigin.DROPI for e in facts)

    def test_weight_collected_when_present(self):
        """Weight should be collected if available."""
        evidences = self.collector.collect_from_dropi(_product())
        weight_ev = [e for e in evidences if e.field == "weight_kg"]
        assert len(weight_ev) == 1
        assert weight_ev[0].value == 0.5

    def test_images_collected(self):
        """Each image URL should be a separate evidence."""
        evidences = self.collector.collect_from_dropi(_product())
        img_ev = [e for e in evidences if e.field == "image_url"]
        assert len(img_ev) == 1
        assert img_ev[0].value == "https://d39ru7awumhhs2.cloudfront.net/products/test.jpg"


class TestCollectFromMercadoLibre:

    def setup_method(self):
        self.collector = EvidenceCollector()

    def test_competitor_price_with_match_quality(self):
        """Each competitor listing should produce evidence with match quality."""
        competitors = [
            CompetitorListing(title="Polvo Destapa Canerias", price_usd=12.0, url="https://ml.com/1"),
            CompetitorListing(title="Liquido Limpiador Cocina", price_usd=8.0, url="https://ml.com/2"),
        ]
        evidences = self.collector.collect_from_mercadolibre(_product(), competitors)
        prices = [e for e in evidences if e.field == "competitor_price"]
        assert len(prices) == 2
        assert all(e.match_quality is not None for e in prices)
        assert all(e.origin == DataOrigin.MERCADOLIBRE for e in prices)

    def test_empty_competitors(self):
        """No competitors should return empty list."""
        evidences = self.collector.collect_from_mercadolibre(_product(), [])
        assert evidences == []


class TestCollectFromGeminiSearch:

    def setup_method(self):
        self.collector = EvidenceCollector()

    def test_buyer_data_collected(self):
        """Buyer concerns and positives should become evidence."""
        buyer_data = {
            "buyer_concerns": ["Se disuelve mal", "Olor fuerte"],
            "buyer_positives": ["Funciona rapido"],
            "real_reviews": ["Me sirvio para la taza del bano"],
            "sources_used": ["https://foro.com/destapadores"],
        }
        evidences = self.collector.collect_from_gemini_search(
            buyer_data, buyer_data["sources_used"]
        )
        concerns = [e for e in evidences if e.field == "buyer_concern"]
        positives = [e for e in evidences if e.field == "buyer_positive"]
        reviews = [e for e in evidences if e.field == "real_review"]

        assert len(concerns) == 2
        assert len(positives) == 1
        assert len(reviews) == 1
        assert all(e.origin == DataOrigin.GOOGLE_SEARCH for e in evidences)
        assert all(e.confidence == 0.7 for e in evidences)  # has sources

    def test_lower_confidence_without_sources(self):
        """Without source URLs, confidence should be lower."""
        evidences = self.collector.collect_from_gemini_search(
            {"buyer_concerns": ["Problema generico"]}, sources=None
        )
        assert evidences[0].confidence == 0.5


class TestImageQualityAssessment:

    def setup_method(self):
        self.collector = EvidenceCollector()

    def test_cloudfront_image_is_clean(self):
        img = self.collector.assess_image_quality(
            "https://d39ru7awumhhs2.cloudfront.net/products/abc.jpg"
        )
        assert img.is_clean is True
        assert img.is_product_only is True

    def test_placeholder_is_not_clean(self):
        img = self.collector.assess_image_quality("https://placeholder.com/img")
        assert img.is_clean is False
