import asyncio
import argparse
import sys
import os
from dotenv import load_dotenv

# Ensure the parent directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rich.console import Console
from rich.panel import Panel
from src.application.intelligence.analyze_competitor import AnalyzeCompetitorUseCase

load_dotenv()
console = Console()

async def main():
    parser = argparse.ArgumentParser(description="Analiza la Landing Page de un competidor usando MarkItDown y Gemini")
    parser.add_argument("--url", type=str, required=True, help="URL de la tienda competidora")
    
    args = parser.parse_args()
    url = args.url
    
    console.print(f"[bold cyan]Analizando competidor: {url}[/bold cyan]")
    
    try:
        use_case = AnalyzeCompetitorUseCase()
        with console.status("[bold yellow]Descargando página con MarkItDown y analizando con Gemini...[/bold yellow]"):
            result = await use_case.execute(url)
            
        console.print(Panel.fit(
            f"[bold green]Titular Encontrado:[/bold green] {result.headline_found}\n\n"
            f"[bold green]Precio Detectado:[/bold green] ${result.price_found_usd:.2f}\n\n"
            f"[bold red]Dolores Atacados (Pain Points):[/bold red]\n- " + "\n- ".join(result.pain_points_addressed) + "\n\n"
            f"[bold blue]Beneficios Destacados:[/bold blue]\n- " + "\n- ".join(result.benefits_highlighted) + "\n\n"
            f"[bold magenta]Recomendaciones para GANARLES:[/bold magenta]\n- " + "\n- ".join(result.improvement_recommendations),
            title="Reporte de Inteligencia Competitiva"
        ))
        
    except Exception as e:
        console.print(f"[bold red]Error durante el análisis:[/bold red] {e}")

if __name__ == "__main__":
    asyncio.run(main())
