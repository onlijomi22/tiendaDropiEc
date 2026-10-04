"""Use Case: Synchronize AI-enriched products directly to the Next.js frontend dataset.

Writes the structured product data, marketing copy, and AI reviews directly to
frontend/src/data/products.json, serving as a static database for compile-time rendering.
"""

import json
from pathlib import Path
from src.domain.products.entities import Product
from src.shared.logger import logger

# Theme mapping based on category names
CATEGORY_THEMES = {
    "hogar": "pink",
    "defensa personal": "blue",
    "seguridad": "blue",
    "salud": "green",
    "cocina": "orange",
    "tecnologia": "blue",
    "belleza": "pink",
}

class SyncFrontendUseCase:
    """Synchronizes enriched product data to the Next.js frontend."""

    def __init__(self, frontend_dir: str = "frontend") -> None:
        self.frontend_dir = Path(frontend_dir)
        self.products_json_path = self.frontend_dir / "src" / "data" / "products.json"

    def _load_enriched_images(self, product_id: str) -> list[str] | None:
        """Load active (clean) images from enriched data if available."""
        enriched_path = self.frontend_dir / "src" / "data" / "enriched" / f"{product_id}.json"
        if not enriched_path.exists():
            return None
        try:
            with open(enriched_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            images = data.get("images", [])
            active = [img["url"] for img in images if img.get("is_clean") and img.get("is_product_only")]
            return active if active else None
        except Exception:
            return None

    def _load_enriched_trust_signals(self, product_id: str) -> list[str] | None:
        """Load trust signals from enriched category config."""
        enriched_path = self.frontend_dir / "src" / "data" / "enriched" / f"{product_id}.json"
        if not enriched_path.exists():
            return None
        try:
            with open(enriched_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cc = data.get("category_config")
            if cc and cc.get("trust_signals"):
                return cc["trust_signals"]
            return None
        except Exception:
            return None

    def execute(
        self,
        product: Product,
        ai_copy: dict,
        ai_reviews: list[dict],
        custom_slug: str | None = None
    ) -> str:
        """Saves a product with its copies and reviews into products.json.

        Args:
            product: The Dropi Product entity.
            ai_copy: Gemini-generated copywriting structures (headline, bullet points, etc.).
            ai_reviews: Gemini-generated reviews list.
            custom_slug: Custom slug to override the product name slug.

        Returns:
            The category slug and product slug path (e.g. '/cocina/sarten-sanduches').
        """
        category_clean = product.category.lower().strip()
        category_slug = category_clean.replace(" ", "-").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        
        # Determine theme color
        theme_color = CATEGORY_THEMES.get(category_clean, "blue")

        # Generate product slug
        if custom_slug:
            product_slug = custom_slug.strip().lower()
        else:
            product_slug = product.name.lower().strip()
            # Clean special chars from slug
            for char in [" ", "/", "\\", "?", "&", "=", "%", "#", '"', "'", "(", ")", ",", "."]:
                product_slug = product_slug.replace(char, "-")
            # Clean accents
            product_slug = product_slug.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
            # Remove double hyphens
            while "--" in product_slug:
                product_slug = product_slug.replace("--", "-")
            product_slug = product_slug.strip("-")

        # Determine if it has variants (clothing/footwear)
        has_variants = category_clean in ["moda", "ropa", "zapatos", "calzado", "vestuario"]

        # Prepare payload matching frontend schema
        product_payload = {
            "id": product.id,
            "slug": product_slug,
            "name": product.name,
            "category": product.category,
            "categorySlug": category_slug,
            "themeColor": theme_color,
            "hasVariants": has_variants,
            "price": ai_copy.get("suggested_price_usd", product.suggested_price),
            "dropiPrice": product.dropi_price,
            "stock": product.stock,
            "supplierId": product.supplier_id,
            "supplierName": product.supplier_name,
            "images": self._load_enriched_images(product.id) or product.images,
            "trustSignals": self._load_enriched_trust_signals(product.id) or [],
            "headline": ai_copy.get("landing_headline", product.name),
            "subheadline": ai_copy.get("landing_subheadline", "¡Solución revolucionaria para tu día a día!"),
            "tiktokAdCopy": ai_copy.get("tiktok_script", ""),
            "bulletPoints": ai_copy.get("benefits", [
                "Calidad premium garantizada.",
                "Envío gratis a todo el Ecuador.",
                "Pago contra entrega."
            ]),
            "faqs": ai_copy.get("faqs", [
                {
                    "question": "¿El envío tiene costo?",
                    "answer": "No, el envío es 100% gratuito a todo el país."
                },
                {
                    "question": "¿Cómo funciona el pago contra entrega?",
                    "answer": "Pagas en efectivo al repartidor al momento de recibir el producto en tu casa."
                }
            ]),
            "comparisonItems": ai_copy.get("comparison_items", [
                {"feature": "Calidad Premium Garantizada", "ourProduct": True, "others": False},
                {"feature": "Envío Gratis a todo Ecuador", "ourProduct": True, "others": False},
                {"feature": "Pago Contra Entrega Seguro", "ourProduct": True, "others": False}
            ]),
            "statMetrics": ai_copy.get("stat_metrics", [
                {"percentage": "95%", "text": "De nuestros clientes recomiendan este producto por su excelente calidad."},
                {"percentage": "98%", "text": "Volverían a elegirnos por nuestro servicio de pago contra entrega seguro."}
            ]),
            "reviews": ai_reviews or [
                {
                    "name": "María G.",
                    "rating": 5,
                    "text": "¡Excelente producto! Llegó muy rápido y es exactamente como en las fotos.",
                    "date": "Hace 2 días",
                    "verified": True
                }
            ]
        }

        # Create directories if they do not exist
        self.products_json_path.parent.mkdir(parents=True, exist_ok=True)

        # Load existing data
        products_db = {}
        if self.products_json_path.exists():
            try:
                with open(self.products_json_path, "r", encoding="utf-8") as f:
                    products_db = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read existing products.json: {e}. Recreating database.")

        # Key is category/slug
        db_key = f"{category_slug}/{product_slug}"
        products_db[db_key] = product_payload

        # Write back database
        with open(self.products_json_path, "w", encoding="utf-8") as f:
            json.dump(products_db, f, indent=2, ensure_ascii=False)

        logger.info(f"Synchronized product '{product.name}' to frontend at dynamic route: /{category_slug}/{product_slug}")
        return f"/{category_slug}/{product_slug}"
