"""Enrich a single product using the V2 evidence-based pipeline.

Usage:
    python scripts/enrich_v2_single.py --id 106937

Outputs:
    - Saves EnrichedProduct JSON to frontend/src/data/enriched/<product_id>.json
    - Prints ENRICHED_PATH=<path> on success
"""

import asyncio
import argparse
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from src.application.enrichment.enrich_product_v2 import EnrichProductV2UseCase, EnrichProductV2Input
from src.domain.products.entities import Product
from src.shared.logger import setup_logger, logger


def _load_product(product_id: str) -> Product | None:
    """Load product from pending_approval.json or products.json."""
    # Try pending first
    pending_file = os.path.join(os.getcwd(), "frontend", "src", "data", "pending_approval.json")
    if os.path.exists(pending_file):
        with open(pending_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if product_id in data:
            p = data[product_id]
            return Product(
                id=p["id"], name=p["name"], category=p["category"],
                dropi_price=p["dropi_price"], suggested_price=p["suggested_price"],
                stock=p["stock"], supplier_id=p.get("supplier_id", "pending"),
                supplier_name=p.get("supplier_name", "Desconocido"),
                images=p.get("images", ["https://placeholder.com/img"]),
                description=p.get("description", p["name"]),
            )

    # Try products.json
    products_file = os.path.join(os.getcwd(), "frontend", "src", "data", "products.json")
    if os.path.exists(products_file):
        with open(products_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        for key, p in data.items():
            if str(p.get("id")) == product_id:
                return Product(
                    id=str(p["id"]), name=p["name"], category=p["category"],
                    dropi_price=p["dropiPrice"], suggested_price=p["price"],
                    stock=p.get("stock", 0), supplier_id=p.get("supplierId", "unknown"),
                    supplier_name=p.get("supplierName", "unknown"),
                    images=p.get("images", ["https://placeholder.com/img"]),
                    description=p.get("headline", p["name"]),
                )
    return None


async def main():
    parser = argparse.ArgumentParser(description="Enrich product with V2 pipeline")
    parser.add_argument("--id", type=str, required=True, help="Product ID")
    parser.add_argument("--price", type=float, default=None, help="Override sale price")
    args = parser.parse_args()

    setup_logger()

    product = _load_product(args.id)
    if not product:
        print(f"ERROR: Product {args.id} not found", file=sys.stderr)
        sys.exit(1)

    logger.info(f"Enriching product: {product.name} (V2)")

    uc = EnrichProductV2UseCase()
    result = await uc.execute(EnrichProductV2Input(
        product=product,
        target_sale_price=args.price,
    ))

    # Save enriched product JSON
    enriched_dir = os.path.join(os.getcwd(), "frontend", "src", "data", "enriched")
    os.makedirs(enriched_dir, exist_ok=True)
    output_path = os.path.join(enriched_dir, f"{product.id}.json")

    enriched_data = result.model_dump(mode="json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(enriched_data, f, indent=2, ensure_ascii=False, default=str)

    print(f"ENRICHED_PATH={output_path}")
    logger.info(f"Saved EnrichedProduct to {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
