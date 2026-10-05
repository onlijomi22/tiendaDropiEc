"""Generate product ad creatives using both template and Gemini approaches.

Usage:
    python scripts/generate_creatives.py --id 17521
    python scripts/generate_creatives.py --id 17521 --method template
    python scripts/generate_creatives.py --id 17521 --method gemini
    python scripts/generate_creatives.py --id 17521 --method both
"""

import asyncio
import argparse
import sys
import os
import json
import io

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.panel import Panel

from src.infrastructure.creatives.template_renderer import TemplateRenderer
from src.infrastructure.creatives.gemini_creative import GeminiCreativeGenerator
from src.shared.logger import setup_logger

console = Console(force_terminal=True)


async def main():
    parser = argparse.ArgumentParser(description="Generate product ad creatives")
    parser.add_argument("--id", type=str, required=True, help="Product ID")
    parser.add_argument("--method", type=str, default="both", choices=["template", "gemini", "both"])
    parser.add_argument("--palette", type=str, default="gold", choices=["gold", "pink", "blue", "green", "orange", "purple"])
    args = parser.parse_args()

    setup_logger()

    # Load enriched data
    enriched_path = os.path.join(os.getcwd(), "frontend", "src", "data", "enriched", f"{args.id}.json")
    if not os.path.exists(enriched_path):
        console.print(f"[red]No enriched data for {args.id}. Run enrich_v2_single.py first.[/red]")
        return

    with open(enriched_path, "r", encoding="utf-8") as f:
        enriched = json.load(f)

    name = enriched.get("display_name", enriched.get("dropi_name", "Producto"))
    category = enriched.get("category", "")
    price = enriched.get("sale_price", 0)
    headline = enriched.get("display_name", name)

    # Get best headline from copy if exists
    products_path = os.path.join(os.getcwd(), "frontend", "src", "data", "products.json")
    if os.path.exists(products_path):
        with open(products_path) as f:
            prods = json.load(f)
        for k, v in prods.items():
            if str(v.get("id")) == str(args.id) and v.get("headline"):
                headline = v["headline"]
                break

    # Get benefits
    benefits = [b["text"] for b in enriched.get("benefits", []) if b.get("confidence", 0) >= 0.4]
    if not benefits:
        benefits = ["Envio gratis a todo Ecuador", "Pago contra entrega", "Calidad garantizada"]

    # Get trust signals
    trust_signals = enriched.get("category_config", {}).get("trust_signals", [])
    if not trust_signals:
        trust_signals = ["Envio gratis", "Pago al recibir", "Garantia"]

    # Get image
    images = enriched.get("images", [])
    active_images = [img["url"] for img in images if img.get("is_clean")]
    product_image = active_images[0] if active_images else (images[0]["url"] if images else "")

    if not product_image:
        console.print("[red]No product image available[/red]")
        return

    console.print(Panel(
        f"[bold]{name}[/bold]\n"
        f"Headline: {headline}\n"
        f"Precio: ${price}\n"
        f"Imagen: ...{product_image[-50:]}\n"
        f"Metodo: {args.method}",
        title="Generando creatives",
        border_style="cyan",
    ))

    output_dir = os.path.join(os.getcwd(), "frontend", "src", "data", "creatives")
    os.makedirs(output_dir, exist_ok=True)

    generated = []

    # Camino A — Template
    if args.method in ("template", "both"):
        renderer = TemplateRenderer()
        for size in ["feed", "story", "meta_ad"]:
            out = os.path.join(output_dir, f"{args.id}_template_{size}.png")
            try:
                path = await renderer.render(
                    headline=headline,
                    subheadline=f"{name} - Envio gratis a todo Ecuador",
                    product_image_url=product_image,
                    price=price,
                    benefits=benefits[:3],
                    trust_signals=trust_signals[:3],
                    size=size,
                    palette=args.palette,
                    output_path=out,
                )
                generated.append(("TEMPLATE", size, path))
                console.print(f"  [green]Template {size}:[/green] {path}")
            except Exception as e:
                console.print(f"  [red]Template {size} failed:[/red] {e}")

    # Camino B — Gemini
    if args.method in ("gemini", "both"):
        gemini = GeminiCreativeGenerator()
        out = os.path.join(output_dir, f"{args.id}_gemini.png")
        try:
            path = await gemini.generate(
                product_image_url=product_image,
                product_name=name,
                headline=headline,
                benefits=benefits[:3],
                price=price,
                category=category,
                output_path=out,
            )
            if path:
                generated.append(("GEMINI", "ai_generated", path))
                console.print(f"  [green]Gemini AI:[/green] {path}")
            else:
                console.print("  [yellow]Gemini: No image generated[/yellow]")
        except Exception as e:
            console.print(f"  [red]Gemini failed:[/red] {e}")

    # Summary
    console.print(f"\n[bold]Generados: {len(generated)} creatives[/bold]")
    for method, size, path in generated:
        console.print(f"  [{method}] {size}: {path}")


if __name__ == "__main__":
    asyncio.run(main())
