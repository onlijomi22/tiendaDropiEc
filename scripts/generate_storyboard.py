"""Generate a TikTok video storyboard from an enriched product.

Usage:
    python scripts/generate_storyboard.py --id 17521

Reads the enriched product JSON and generates a detailed
shot-by-shot storyboard for filming a TikTok ad.
"""

import asyncio
import argparse
import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box

from src.infrastructure.ai.gemini_adapter import GeminiAdapter
from src.shared.logger import setup_logger

console = Console(force_terminal=True)


async def main():
    parser = argparse.ArgumentParser(description="Generate TikTok storyboard")
    parser.add_argument("--id", type=str, required=True)
    args = parser.parse_args()

    setup_logger()

    # Load enriched product
    enriched_path = os.path.join(os.getcwd(), "frontend", "src", "data", "enriched", f"{args.id}.json")
    if not os.path.exists(enriched_path):
        console.print(f"[red]No enriched data for product {args.id}. Run enrich_v2_single.py first.[/red]")
        return

    with open(enriched_path, "r", encoding="utf-8") as f:
        enriched = json.load(f)

    product_name = enriched.get("display_name", enriched.get("dropi_name", "Producto"))
    category = enriched.get("category", "")
    price = enriched.get("sale_price", 0)
    benefits = [b["text"] for b in enriched.get("benefits", [])]
    concerns = [c["text"] for c in enriched.get("buyer_concerns", [])]
    positives = [p["text"] for p in enriched.get("buyer_positives", [])]

    # Get category config
    cat_config = enriched.get("category_config", {})
    primary_objection = cat_config.get("primary_objection", "")
    trust_signals = cat_config.get("trust_signals", [])

    prompt = f"""Eres un director creativo de videos para TikTok Ads en Ecuador.
Genera un STORYBOARD detallado toma por toma para filmar un video de 30 segundos.

PRODUCTO: {product_name}
CATEGORIA: {category}
PRECIO: ${price}
BENEFICIOS REALES: {json.dumps(benefits, ensure_ascii=False)}
PREOCUPACIONES DE COMPRADORES: {json.dumps(concerns, ensure_ascii=False)}
POSITIVOS: {json.dumps(positives, ensure_ascii=False)}
OBJECION PRINCIPAL: {primary_objection}
SENALES DE CONFIANZA: {json.dumps(trust_signals, ensure_ascii=False)}

Responde en JSON con este formato exacto:
{{
    "hook": "Texto exacto de los primeros 3 segundos (lo que se dice/muestra)",
    "total_duration_seconds": 30,
    "shots": [
        {{
            "shot_number": 1,
            "duration_seconds": 3,
            "type": "HOOK",
            "camera": "Primer plano del problema",
            "action": "Que hace la persona en cuadro",
            "text_overlay": "Texto que aparece en pantalla",
            "audio": "Que se dice o que musica suena",
            "props_needed": "Que objetos necesitas tener listos"
        }}
    ],
    "filming_tips": [
        "Tip practico para grabar con celular"
    ],
    "equipment_needed": ["celular", "luz natural", "etc"],
    "estimated_filming_time_minutes": 15
}}"""

    console.print(Panel(f"[bold]{product_name}[/bold]\nGenerando storyboard...", border_style="cyan"))

    adapter = GeminiAdapter()
    data = await adapter.generate_json(prompt)

    if not data or "shots" not in data:
        console.print("[red]Error generando storyboard[/red]")
        return

    # Display storyboard
    console.print(Panel(f"[bold yellow]HOOK (3s):[/bold yellow] {data.get('hook', '')}", border_style="yellow"))

    shot_table = Table(title=f"Storyboard — {product_name} ({data.get('total_duration_seconds', 30)}s)", box=box.ROUNDED)
    shot_table.add_column("#", style="bold cyan", width=3)
    shot_table.add_column("Dur.", width=4)
    shot_table.add_column("Tipo", width=8)
    shot_table.add_column("Camara", width=25)
    shot_table.add_column("Accion", width=30)
    shot_table.add_column("Texto en pantalla", width=25)
    shot_table.add_column("Props", width=20)

    for shot in data.get("shots", []):
        shot_table.add_row(
            str(shot.get("shot_number", "")),
            f"{shot.get('duration_seconds', '')}s",
            shot.get("type", ""),
            shot.get("camera", ""),
            shot.get("action", ""),
            shot.get("text_overlay", ""),
            shot.get("props_needed", ""),
        )

    console.print(shot_table)

    # Tips
    if data.get("filming_tips"):
        console.print(Panel(
            "\n".join(f"  - {tip}" for tip in data["filming_tips"]),
            title="Tips de filmacion",
            border_style="green",
        ))

    # Equipment
    if data.get("equipment_needed"):
        console.print(f"\n[bold]Equipo necesario:[/bold] {', '.join(data['equipment_needed'])}")
        console.print(f"[bold]Tiempo estimado de filmacion:[/bold] {data.get('estimated_filming_time_minutes', '?')} minutos")

    # Save to file
    output_path = os.path.join(os.getcwd(), "frontend", "src", "data", "enriched", f"{args.id}_storyboard.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    console.print(f"\n[dim]Guardado en: {output_path}[/dim]")


if __name__ == "__main__":
    asyncio.run(main())
