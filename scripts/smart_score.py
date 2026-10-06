"""Score products using the smart multi-signal scoring system.

Usage:
    python scripts/smart_score.py --name "Organizador de huevos" --category hogar --cost 8 --price 30 --stock 49
    python scripts/smart_score.py --id 17521
"""

import asyncio
import argparse
import sys
import os
import io
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

from src.application.products.smart_scoring import SmartScoringUseCase
from src.domain.products.entities import Product
from src.shared.logger import setup_logger

console = Console(force_terminal=True)


def _load_from_pending(pid: str) -> Product | None:
    path = os.path.join(os.getcwd(), "frontend", "src", "data", "pending_approval.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if pid not in data:
        return None
    p = data[pid]
    return Product(
        id=p["id"], name=p["name"], category=p["category"],
        dropi_price=p["dropi_price"], suggested_price=p["suggested_price"],
        stock=p["stock"], supplier_id="pending",
        images=p.get("images", ["https://placeholder.com/img"]),
        description=p.get("name", ""),
    )


async def main():
    parser = argparse.ArgumentParser(description="Smart product scoring")
    parser.add_argument("--id", type=str, help="Product ID from pending")
    parser.add_argument("--name", type=str, help="Product name (manual)")
    parser.add_argument("--category", type=str, default="hogar")
    parser.add_argument("--cost", type=float, default=8.0)
    parser.add_argument("--price", type=float, default=30.0)
    parser.add_argument("--stock", type=int, default=50)
    args = parser.parse_args()

    setup_logger()

    if args.id:
        product = _load_from_pending(args.id)
        if not product:
            console.print(f"[red]Product {args.id} not found[/red]")
            return
    elif args.name:
        product = Product(
            id="MANUAL", name=args.name, category=args.category,
            dropi_price=args.cost, suggested_price=args.price, stock=args.stock,
            supplier_id="manual", images=["https://placeholder.com/img"],
            description=args.name,
        )
    else:
        console.print("[red]Usa --id o --name[/red]")
        return

    console.print(Panel(
        f"[bold]{product.name}[/bold]\n"
        f"Costo: ${product.dropi_price} | Precio: ${product.suggested_price} | Stock: {product.stock}",
        title="Smart Scoring", border_style="cyan",
    ))

    uc = SmartScoringUseCase()
    result = await uc.score_product(product)

    # Breakdown table
    table = Table(title="Score Breakdown", box=box.ROUNDED)
    table.add_column("Componente", style="cyan")
    table.add_column("Puntos", style="white", justify="right")
    table.add_column("Max", style="dim", justify="right")
    table.add_column("Detalle", style="dim")

    ctx = result.context
    for comp, pts in result.breakdown.items():
        max_pts = {"margin": 25, "competition": 20, "trend": 15, "social": 15, "images": 10, "stock": 10, "supplier": 5}[comp]
        detail = {
            "margin": f"{ctx.margin_pct:.1f}% (neto ${ctx.net_profit:.2f})",
            "competition": f"{ctx.competitor_count} vendedores ({ctx.competition_level.value})",
            "trend": f"Google Trends {ctx.trend_score:.2f} ({'subiendo' if ctx.trend_rising else 'estable'}, avg:{ctx.trend_avg_interest:.0f})",
            "social": f"{ctx.social_demand} (score {ctx.social_score:.2f}, rec: {ctx.social_recommendation})",
            "images": f"{ctx.clean_images} limpias de {ctx.total_images}",
            "stock": f"{ctx.stock} unidades",
            "supplier": "rating no disponible (default)",
        }[comp]

        color = "green" if pts >= max_pts * 0.7 else "yellow" if pts >= max_pts * 0.4 else "red"
        table.add_row(comp.upper(), f"[{color}]{pts:.1f}[/{color}]", str(max_pts), detail)

    table.add_row("", "", "", "")
    rec = result.score.recommendation.value
    rec_color = "green" if rec == "BUY" else "yellow" if rec == "WATCH" else "red"
    table.add_row("[bold]TOTAL[/bold]", f"[bold {rec_color}]{result.score.total_score:.1f}[/bold {rec_color}]", "100", f"[bold {rec_color}]{rec}[/bold {rec_color}]")

    console.print(table)
    console.print(f"\n[dim]{result.score.reasoning}[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
