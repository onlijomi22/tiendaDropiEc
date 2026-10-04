"""CLI script: Analyze a single Dropi product with full market intelligence.

Usage:
    python scripts/analyze_product.py --name "Licuadora Sokany 2 en 1" \
        --category cocina --cost 28 --price 52 --stock 177

Output:
    1. RAW DATA: Competition from MercadoLibre + buyer insights
    2. DRAFT COPY: Landing headline, benefits, TikTok script, Meta ads
    3. VERDICT: Viable or not, with reason

Requires GEMINI_API_KEY in .env
"""

import asyncio
import argparse
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from src.shared.logger import setup_logger
from src.domain.products.entities import Product
from src.application.intelligence.enrich_product import (
    EnrichProductInput,
    EnrichProductUseCase,
)

console = Console()


def build_product(args) -> Product:
    """Build a Product entity from CLI args."""
    return Product(
        id=f"CLI-{args.name[:8].replace(' ', '-').upper()}",
        name=args.name,
        category=args.category,
        dropi_price=args.cost,
        suggested_price=args.price,
        stock=args.stock,
        supplier_id="manual",
        images=["https://placeholder.com/img"],
        description=args.name,
    )


def print_raw_data(result) -> None:
    """Print market insight (raw data section)."""
    console.print()
    console.print(Panel("📊 DATOS REALES DEL MERCADO", style="bold cyan"))

    insight = result.market_insight

    # Competition table
    if insight.competitors:
        table = Table(title=f"Competidores en MercadoLibre Ecuador ({insight.competition_count} encontrados)")
        table.add_column("Producto", style="white", max_width=40)
        table.add_column("Precio", style="green", justify="right")
        table.add_column("Ventas", style="yellow", justify="right")
        for c in insight.competitors[:5]:
            table.add_row(c.title[:40], f"${c.price_usd:.2f}", str(c.sales_count))
        console.print(table)
        console.print(f"  Precio promedio competencia: [bold]${insight.avg_competitor_price:.2f}[/bold]")
        console.print(f"  Nivel de competencia: [bold]{insight.competition_level.value}[/bold]")
    else:
        console.print("  [yellow]No se encontraron competidores en MercadoLibre[/yellow]")

    console.print()

    # Buyer concerns
    if insight.buyer_concerns:
        console.print("[bold red]⚠️ Miedos reales de compradores:[/bold red]")
        for concern in insight.buyer_concerns:
            console.print(f"  • {concern}")

    console.print()

    # Buyer positives
    if insight.buyer_positives:
        console.print("[bold green]✅ Lo que los compradores valoran:[/bold green]")
        for pos in insight.buyer_positives:
            console.print(f"  • {pos}")


def print_copy_draft(result) -> None:
    """Print the AI-generated copy draft."""
    console.print()
    console.print(Panel("✍️  BORRADOR DE COPY (para revisión humana)", style="bold yellow"))

    draft = result.copy_draft

    console.print(f"[bold]LANDING HEADLINE:[/bold] {draft.landing_headline}")
    console.print(f"[bold]SUBHEADLINE:[/bold] {draft.landing_subheadline}")
    console.print()

    console.print("[bold]BENEFICIOS:[/bold]")
    for i, b in enumerate(draft.benefits, 1):
        console.print(f"  {i}. {b}")
    console.print()

    console.print("[bold]RESEÑAS ILUSTRATIVAS:[/bold]")
    for q in draft.review_quotes:
        console.print(f'  "{q}"')
    console.print()

    console.print("[bold]MANEJO DE OBJECIONES:[/bold]")
    for obj in draft.objection_handlers:
        console.print(f"  → {obj}")
    console.print()

    console.print(Panel(
        f"[bold]TIKTOK HOOK:[/bold] {draft.tiktok_hook}\n\n"
        f"[bold]GUIÓN TIKTOK:[/bold]\n{draft.tiktok_script}",
        title="🎬 TikTok Ads",
        style="magenta"
    ))
    console.print()

    console.print(Panel(
        f"[bold]Headline:[/bold] {draft.meta_headline}\n"
        f"[bold]Body:[/bold] {draft.meta_body}",
        title="📱 Meta Ads",
        style="blue"
    ))
    console.print()

    console.print(f"[bold]Precio sugerido:[/bold] ${draft.suggested_price_usd:.2f} "
                 f"(margen {draft.suggested_margin_pct:.1f}%)")
    console.print()

    console.print(Panel(
        f"[yellow]⚠️ REVISAR ANTES DE PUBLICAR:[/yellow]\n{draft.human_review_notes}",
        style="yellow"
    ))


def print_verdict(result) -> None:
    """Print viability verdict."""
    console.print()
    style = "bold green" if result.viable else "bold red"
    verdict = "✅ VIABLE — Vale la pena vender" if result.viable else "❌ NO VIABLE — Ver razones"
    console.print(Panel(result.viability_reason, title=verdict, style=style))


async def main(args) -> None:
    """Run product intelligence analysis."""
    setup_logger()
    product = build_product(args)

    console.print(Panel(
        f"Analizando: [bold]{product.name}[/bold]\n"
        f"Costo Dropi: ${product.dropi_price:.2f} | "
        f"Precio venta: ${args.price:.2f} | "
        f"Stock: {product.stock}",
        title="🔍 TiendaDropiEc — Product Intelligence",
        style="cyan"
    ))

    use_case = EnrichProductUseCase()
    result = await use_case.execute(
        EnrichProductInput(product=product, target_sale_price=args.price)
    )

    print_raw_data(result)
    print_copy_draft(result)
    print_verdict(result)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Analyze a Dropi product with real market intelligence"
    )
    parser.add_argument("--name", required=True, help="Product name")
    parser.add_argument("--category", required=True, help="Product category")
    parser.add_argument("--cost", type=float, required=True, help="Dropi cost price")
    parser.add_argument("--price", type=float, required=True, help="Target sale price")
    parser.add_argument("--stock", type=int, default=50, help="Available stock")
    args = parser.parse_args()
    asyncio.run(main(args))
