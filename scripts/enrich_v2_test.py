"""Test script for the V2 evidence-based enrichment pipeline.

Usage:
    python scripts/enrich_v2_test.py --id 106937
    python scripts/enrich_v2_test.py --name "Licuadora Portatil" --category cocina --cost 10 --price 30 --stock 50
"""

import asyncio
import argparse
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.application.enrichment.enrich_product_v2 import EnrichProductV2UseCase, EnrichProductV2Input
from src.domain.enrichment.entities import DataType, MatchQuality
from src.domain.products.entities import Product
from src.shared.logger import setup_logger

console = Console()


def _load_from_pending(product_id: str) -> Product | None:
    """Try to load a product from pending_approval.json."""
    pending_file = os.path.join(os.getcwd(), "frontend", "src", "data", "pending_approval.json")
    if not os.path.exists(pending_file):
        return None
    with open(pending_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    if product_id not in data:
        return None
    p = data[product_id]
    return Product(
        id=p["id"], name=p["name"], category=p["category"],
        dropi_price=p["dropi_price"], suggested_price=p["suggested_price"],
        stock=p["stock"], supplier_id="pending",
        images=p.get("images", ["https://placeholder.com/img"]),
        description=p.get("name", ""),
    )


def _load_from_products_json(product_id: str) -> Product | None:
    """Try to load from products.json (already published)."""
    products_file = os.path.join(os.getcwd(), "frontend", "src", "data", "products.json")
    if not os.path.exists(products_file):
        return None
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
    parser = argparse.ArgumentParser(description="Test V2 enrichment pipeline")
    parser.add_argument("--id", type=str, help="Product ID from pending_approval.json or products.json")
    parser.add_argument("--name", type=str, help="Product name (manual mode)")
    parser.add_argument("--category", type=str, default="hogar")
    parser.add_argument("--cost", type=float, default=5.0)
    parser.add_argument("--price", type=float, default=20.0)
    parser.add_argument("--stock", type=int, default=50)
    args = parser.parse_args()

    setup_logger()

    # Build product
    if args.id:
        product = _load_from_pending(args.id) or _load_from_products_json(args.id)
        if not product:
            console.print(f"[red]Producto {args.id} no encontrado en pending ni products.json[/red]")
            return
    elif args.name:
        product = Product(
            id="MANUAL-001", name=args.name, category=args.category,
            dropi_price=args.cost, suggested_price=args.price, stock=args.stock,
            supplier_id="manual", images=["https://placeholder.com/img"],
            description=args.name,
        )
    else:
        console.print("[red]Usa --id <ID> o --name 'Nombre del producto'[/red]")
        return

    console.print(Panel(
        f"[bold]{product.name}[/bold]\n"
        f"ID: {product.id} | Cat: {product.category} | "
        f"Costo: ${product.dropi_price} | Precio: ${product.suggested_price} | Stock: {product.stock}",
        title="Producto a enriquecer (V2)",
        border_style="cyan",
    ))

    # Run V2 pipeline
    uc = EnrichProductV2UseCase()
    result = await uc.execute(EnrichProductV2Input(product=product))

    # === REPORT ===

    # 1. Evidence summary
    console.print("\n")
    evidence_table = Table(title="Resumen de Evidencias", box=box.ROUNDED)
    evidence_table.add_column("Metrica", style="cyan")
    evidence_table.add_column("Valor", style="white")
    evidence_table.add_row("Total evidencias", str(result.evidence_count))
    evidence_table.add_row("Confidence promedio", f"{result.avg_confidence:.3f}")
    evidence_table.add_row("Competidores encontrados", str(result.competition_count))
    evidence_table.add_row("Nivel competencia", result.competition_level.value)
    evidence_table.add_row("Precio competencia avg",
                           f"${result.competitor_avg_price:.2f}" if result.competitor_avg_price else "N/A")
    evidence_table.add_row("Confidence precio comp.", f"{result.competitor_price_confidence:.3f}")
    console.print(evidence_table)

    # 2. Viability
    viable_color = "green" if result.viable else "red"
    console.print(Panel(
        f"[bold {viable_color}]{'VIABLE' if result.viable else 'NO VIABLE'}[/bold {viable_color}]\n\n"
        f"Margen: {result.margin_pct}% | Ganancia neta: ${result.net_profit:.2f}\n"
        f"{result.viability_reason}",
        title="Viabilidad",
        border_style=viable_color,
    ))

    # 3. Images
    img_table = Table(title="Imagenes", box=box.ROUNDED)
    img_table.add_column("URL (ultimos 40 chars)", style="dim")
    img_table.add_column("Limpia", style="green")
    img_table.add_column("Solo producto", style="green")
    img_table.add_column("Texto chino", style="red")
    img_table.add_column("Telefono", style="red")
    for img in result.images:
        img_table.add_row(
            f"...{img.url[-40:]}" if len(img.url) > 40 else img.url,
            "SI" if img.is_clean else "NO",
            "SI" if img.is_product_only else "NO",
            "SI" if img.has_chinese_text else "-",
            "SI" if img.has_phone_number else "-",
        )
    has_enough = result.has_sufficient_images
    img_table.add_row("", "", "", "", "")
    img_table.add_row(
        f"Imagenes limpias suficientes?",
        f"[{'green' if has_enough else 'red'}]{'SI' if has_enough else 'NO'}[/]",
        "", "", "",
    )
    console.print(img_table)

    # 4. Specs extracted
    if result.specifications:
        spec_table = Table(title="Especificaciones extraidas", box=box.ROUNDED)
        spec_table.add_column("Spec", style="cyan")
        spec_table.add_column("Valor", style="white")
        spec_table.add_column("Confidence", style="yellow")
        for spec in result.specifications:
            spec_table.add_row(spec.name, spec.value, f"{spec.confidence:.2f}")
        console.print(spec_table)

    # 5. Buyer data
    if result.buyer_concerns:
        console.print(Panel(
            "\n".join(f"  - {c.text} [dim](conf: {c.confidence:.2f}, {c.origin.value})[/dim]"
                      for c in result.buyer_concerns),
            title="Preocupaciones de compradores (pasan gate >= 0.6)",
            border_style="yellow",
        ))

    if result.buyer_positives:
        console.print(Panel(
            "\n".join(f"  - {p.text} [dim](conf: {p.confidence:.2f}, {p.origin.value})[/dim]"
                      for p in result.buyer_positives),
            title="Positivos de compradores (pasan gate >= 0.6)",
            border_style="green",
        ))

    # 6. Reviews
    displayable = result.displayable_reviews
    all_reviews = result.real_reviews
    if all_reviews:
        review_text = []
        for r in all_reviews:
            passes = r.confidence >= 0.7
            status = "[green]PASA[/green]" if passes else "[red]FILTRADA[/red]"
            review_text.append(f"  {status} \"{r.text}\" [dim](conf: {r.confidence:.2f})[/dim]")
        console.print(Panel(
            "\n".join(review_text),
            title=f"Reviews ({len(displayable)} pasan gate >= 0.7 de {len(all_reviews)} total)",
            border_style="magenta",
        ))

    # 7. Benefits
    if result.benefits:
        ben_text = []
        for b in result.benefits:
            passes = b.confidence >= 0.4
            status = "[green]MUESTRA[/green]" if passes else "[red]OCULTO[/red]"
            ben_text.append(f"  {status} {b.text} [dim]({b.data_type.value}, conf: {b.confidence:.2f})[/dim]")
        console.print(Panel(
            "\n".join(ben_text),
            title="Beneficios derivados",
            border_style="blue",
        ))

    # 8. Category config
    if result.category_config:
        cc = result.category_config
        console.print(Panel(
            f"Slug: {cc.slug} | Color: {cc.theme_color} | Tono: {cc.tone}\n"
            f"Objecion principal: {cc.primary_objection}\n"
            f"Trust signals: {', '.join(cc.trust_signals)}\n"
            f"Rango precio: ${cc.price_range_min}-${cc.price_range_max}",
            title="Config de categoria",
            border_style="dim",
        ))

    # 9. Human review notes
    if result.human_review_notes:
        console.print(Panel(
            "\n".join(f"  [yellow]![/yellow] {note}" for note in result.human_review_notes),
            title="Notas para el operador",
            border_style="yellow",
        ))
    else:
        console.print("[green]Sin notas de revision pendientes.[/green]")

    # 10. Display name and slug
    console.print(f"\n[bold]Display name:[/bold] {result.display_name}")
    console.print(f"[bold]Slug:[/bold] {result.slug}")
    console.print(f"[bold]Description clean:[/bold] {result.description_clean[:150]}...")


if __name__ == "__main__":
    asyncio.run(main())
