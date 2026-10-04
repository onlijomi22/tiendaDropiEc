"""Use case: Generate marketing copy for a product based on real market data.

Spec: specs/intelligence/product_intelligence.spec.md
CA-INTEL-03: Always return draft copy ready for human review
"""

from __future__ import annotations
from dataclasses import dataclass

from src.domain.business_rules import ESTIMATED_CPA_USD, ESTIMATED_SHIPPING_COST_USD
from src.domain.intelligence.entities import MarketInsight, ProductCopyDraft
from src.domain.products.entities import Product
from src.infrastructure.ai.gemini_adapter import GeminiAdapter
from src.shared.logger import logger


@dataclass
class GenerateProductCopyInput:
    """Input for product copy generation."""
    product: Product
    sale_price: float
    market_insight: MarketInsight


class GenerateProductCopyUseCase:
    """Generate marketing copy based on real market data.

    Uses Gemini to create landing page copy, TikTok scripts,
    and Meta ads copy — all based on real buyer data, not hallucinations.
    """

    def __init__(self, gemini_adapter: GeminiAdapter | None = None) -> None:
        self._gemini = gemini_adapter or GeminiAdapter()

    async def execute(self, inp: GenerateProductCopyInput) -> ProductCopyDraft:
        """Generate copy draft using real market insights.

        Args:
            inp: Product, sale price, and market research data.

        Returns:
            ProductCopyDraft ready for human review.
        """
        product = inp.product
        sale_price = inp.sale_price
        market_insight = inp.market_insight

        margin = (sale_price - product.dropi_price) / sale_price * 100
        net_profit = sale_price - product.dropi_price - ESTIMATED_CPA_USD - ESTIMATED_SHIPPING_COST_USD

        logger.info(f"[GenerateProductCopy] Generating copy for: {product.name}")

        prompt = self._build_prompt(product, sale_price, market_insight)

        try:
            data = await self._gemini.generate_json(prompt)
        except Exception as e:
            logger.error(f"[GenerateProductCopy] Copy generation failed: {e}")
            data = {}

        return ProductCopyDraft(
            product_id=product.id,
            product_name=product.name,
            landing_headline=data.get("landing_headline", f"Consigue tu {product.name}"),
            landing_subheadline=data.get("landing_subheadline", "Pago contra entrega en todo Ecuador"),
            benefits=data.get("benefits", ["Calidad garantizada", "Envio rapido", "Pago al recibir"]),
            review_quotes=data.get("review_quotes", []),
            objection_handlers=data.get("objection_handlers", []),
            comparison_items=data.get("comparison_items", []),
            stat_metrics=data.get("stat_metrics", []),
            tiktok_hook=data.get("tiktok_hook", f"Ya viste este {product.category}?"),
            tiktok_script=data.get("tiktok_script", ""),
            meta_headline=data.get("meta_headline", product.name[:40]),
            meta_body=data.get("meta_body", "Paga cuando lo recibas. Envio a todo Ecuador."),
            is_bulky=data.get("is_bulky", False),
            suggested_price_usd=data.get("suggested_price_usd", sale_price),
            suggested_margin_pct=margin,
            data_sources=market_insight.sources,
            human_review_notes=data.get(
                "human_review_notes",
                "Verificar precios de competencia actualizados y validar beneficios con el producto real."
            ),
        )

    def _build_prompt(
        self, product: Product, sale_price: float, market_insight: MarketInsight
    ) -> str:
        """Build the copywriting prompt with real market data."""
        concerns_text = "\n".join(f"- {c}" for c in market_insight.buyer_concerns)
        positives_text = "\n".join(f"- {p}" for p in market_insight.buyer_positives)
        reviews_text = "\n".join(f"- {r}" for r in market_insight.real_reviews)
        competitors_text = "\n".join(
            f"- {c.title}: ${c.price_usd:.2f}" for c in market_insight.competitors[:3]
        ) or "No se encontraron competidores directos"

        return f"""Eres un experto en copywriting para e-commerce en Ecuador.
Generas copy de ventas basado UNICAMENTE en los datos reales que te doy.

PRODUCTO:
- Nombre: {product.name}
- Categoria: {product.category}
- Precio de venta sugerido: ${sale_price:.2f} USD
- Costo para el vendedor: ${product.dropi_price:.2f} USD
- Pago contra entrega (Dropi Ecuador)
- Descripcion Original del Proveedor: {product.description[:1000]} (Nota: OMITIR numeros de telefono y basura del proveedor. Usa solo los datos utiles).

DATOS REALES DE MERCADO:

Preocupaciones reales de compradores:
{concerns_text or '(no se encontraron datos especificos)'}

Lo que los compradores valoran:
{positives_text or '(no se encontraron datos especificos)'}

RESENAS REALES EXTRAIDAS DE INTERNET:
{reviews_text or '(no se encontraron resenas textuales)'}

Competidores en MercadoLibre Ecuador:
{competitors_text}

INSTRUCCIONES Y MEJORES PRACTICAS (Shopify Conversion Masterclass):
1. **Jerarquia y Movil:** Trafico 60%+ movil en Ecuador. Usa un lenguaje agil, frases cortas y vinetas.
2. **Titular (landing_headline):** JAMAS el nombre del producto. Debe ser un Titular de Beneficio que resuelva directamente el problema u objetivo principal del cliente (Ej: "Despierta sin dolor de espalda").
3. **Subtitulo (landing_subheadline):** Usalo para MATAR LA MAYOR OBJECION y dar seguridad (Ej: "Aprobado por ortopedistas, envio gratis a todo Ecuador").
4. **Beneficios (benefits):** Enumera las transformaciones de vida, no solo caracteristicas tecnicas (No "Bateria 2000mAh", sino "Musica todo el dia sin buscar enchufe"). Si hay sellos/certificaciones, mencionalas.
5. **Voz del Cliente (Prueba Social):** Usa las "RESENAS REALES EXTRAIDAS DE INTERNET" para rellenar las `review_quotes`. NO inventes resenas genericas ("Excelente calidad, lo recomiendo")! Si las resenas reales dicen "me llego rapido y suena durisimo", pon eso. La autenticidad vende.
6. **Seguridad (Gatillo Latino):** Mencionar siempre el Envio Nacional y el Pago Contra Entrega.
7. **Contexto de Trafico:** Para TikTok, el hook (tiktok_hook) de 3 segundos es de vida o muerte; muestra el problema y la solucion al instante.

Responde SOLO en este formato JSON:
{{
    "landing_headline": "titulo principal de la landing (maximo 60 caracteres)",
    "landing_subheadline": "subtitulo que apoya el headline (maximo 120 caracteres)",
    "benefits": [
        "beneficio 1 (basado en datos reales)",
        "beneficio 2",
        "beneficio 3"
    ],
    "review_quotes": [
        "Frase ilustrativa tipo resena 1 (inspirada en datos reales)",
        "Frase ilustrativa tipo resena 2"
    ],
    "objection_handlers": [
        "Respuesta a preocupacion 1",
        "Respuesta a preocupacion 2"
    ],
    "comparison_items": [
        {{"feature": "Caracteristica que nos destaca vs otros", "ourProduct": true, "others": false}},
        {{"feature": "Pago contra entrega", "ourProduct": true, "others": false}}
    ],
    "stat_metrics": [
        {{"percentage": "95%", "text": "De compradores destacan la calidad o alguna ventaja del producto"}}
    ],
    "tiktok_hook": "primera frase del video — primeros 3 segundos",
    "tiktok_script": "guion completo de 30 segundos con indicaciones de toma",
    "meta_headline": "headline Meta Ads (maximo 40 caracteres)",
    "meta_body": "texto cuerpo Meta Ads (maximo 125 caracteres)",
    "suggested_price_usd": precio_recomendado_basado_en_competencia,
    "human_review_notes": "que debe verificar el operador antes de publicar",
    "is_bulky": true_o_false_si_es_mueble_perchero_electrodomestico_pesado_o_grande
}}"""
