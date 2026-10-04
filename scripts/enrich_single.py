import asyncio
import argparse
import sys
import os
import json
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rich.console import Console
from src.application.intelligence.enrich_product import EnrichProductUseCase, EnrichProductInput
from src.infrastructure.frontend.sync_frontend import SyncFrontendUseCase
from src.domain.products.entities import Product
from src.shared.logger import setup_logger

load_dotenv()
console = Console()

async def main():
    parser = argparse.ArgumentParser(description="Enriquece un producto específico y lo pasa al frontend")
    parser.add_argument("--id", type=str, required=True, help="ID del producto a enriquecer")
    args = parser.parse_args()
    
    setup_logger()
    product_id = args.id
    
    pending_file = os.path.join(os.getcwd(), "frontend", "src", "data", "pending_approval.json")
    
    if not os.path.exists(pending_file):
        console.print("[red]No hay archivo de pendientes.[/red]")
        return
        
    with open(pending_file, "r", encoding="utf-8") as f:
        pending_data = json.load(f)
        
    if product_id not in pending_data:
        console.print(f"[red]Producto {product_id} no encontrado en pendientes.[/red]")
        return
        
    prod_data = pending_data[product_id]
    
    product = Product(
        id=prod_data["id"],
        name=prod_data["name"],
        category=prod_data["category"],
        dropi_price=prod_data["dropi_price"],
        suggested_price=prod_data["suggested_price"],
        stock=prod_data["stock"],
        supplier_id="manual",
        images=prod_data["images"],
        description=prod_data["name"],
    )
    
    console.print(f"[yellow]Enriqueciendo producto {product.name}...[/yellow]")
    
    enrich_uc = EnrichProductUseCase()
    sync_uc = SyncFrontendUseCase()
    
    enrich_result = await enrich_uc.execute(
        EnrichProductInput(product=product)
    )
    
    if enrich_result.viable:
        url = sync_uc.execute(
            product=product,
            ai_copy=enrich_result.copy_draft.model_dump(),
            ai_reviews=[{"text": q, "rating": 5, "name": "Cliente Verificado"} for q in enrich_result.copy_draft.review_quotes]
        )
        console.print("[green]Producto enriquecido y guardado exitosamente en products.json.[/green]")
        console.print(f"LANDING_URL={url}")
    elif enrich_result.copy_draft.is_bulky:
        report_path = os.path.join(os.getcwd(), "oportunidades_voluminosas.md")
        with open(report_path, "a", encoding="utf-8") as f:
            f.write(f"## {product.name}\n")
            f.write(f"- **Categoría:** {product.category}\n")
            f.write(f"- **Costo Dropi:** ${product.dropi_price}\n")
            f.write(f"- **Precio Sugerido:** ${enrich_result.copy_draft.suggested_price_usd}\n")
            f.write(f"- **Razón:** Rechazado por volumen por IA\n\n")
        console.print("[yellow]Producto marcado como voluminoso. Movido a oportunidades_voluminosas.md[/yellow]")
    else:
        console.print("[red]El producto ya no es viable tras el análisis de competencia.[/red]")
        
    # Remove from pending
    del pending_data[product_id]
    with open(pending_file, "w", encoding="utf-8") as f:
        json.dump(pending_data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
