"""Decision Engine: evaluates real data and generates recommended actions.

Every recommendation is based on observable data, never on LLM opinions.
Actions are suggestions for the operator — not automatic executions.
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from src.domain.business_rules import (
    CPA_TARGET_USD,
    ESTIMATED_REJECTION_RATE,
    MIN_STOCK_FOR_BUY,
    PAUSE_DAYS_MIN,
    PAUSE_ROAS_THRESHOLD,
    SCALE_DAYS_MIN,
    SCALE_ROAS_THRESHOLD,
    STOCK_ALERT_THRESHOLD,
)
from src.shared.logger import logger


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class ActionType(str, Enum):
    PAUSE_CAMPAIGN = "PAUSE_CAMPAIGN"
    SCALE_BUDGET = "SCALE_BUDGET"
    REJECT_PRODUCT = "REJECT_PRODUCT"
    REFRESH_CREATIVE = "REFRESH_CREATIVE"
    ALERT_STOCK = "ALERT_STOCK"
    ALERT_PRICING = "ALERT_PRICING"
    EXPLORE_CATEGORY = "EXPLORE_CATEGORY"
    REPLICATE_WINNER = "REPLICATE_WINNER"
    CONFIRM_PENDING = "CONFIRM_PENDING"


class ActionPriority(str, Enum):
    CRITICAL = "CRITICAL"       # Losing money — act now
    HIGH = "HIGH"               # Opportunity or risk
    MEDIUM = "MEDIUM"           # Optimization
    LOW = "LOW"                 # Nice to have


class Action(BaseModel):
    """A recommended action for the operator."""
    id: str = Field(default_factory=lambda: f"ACT-{datetime.utcnow().strftime('%H%M%S')}-{id(object()) % 1000}")
    action_type: ActionType
    priority: ActionPriority
    product_id: str | None = None
    product_name: str | None = None
    campaign_id: str | None = None
    reason: str
    data: dict = Field(default_factory=dict)
    suggested_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "PENDING"  # PENDING, EXECUTED, DISMISSED


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class DecisionEngine:
    """Evaluates orders, campaigns, and products to generate actions."""

    def __init__(
        self,
        orders_path: str = "frontend/src/data/orders.json",
        campaigns_path: str = "frontend/src/data/campaigns.json",
        products_path: str = "frontend/src/data/products.json",
        pending_path: str = "frontend/src/data/pending_approval.json",
    ) -> None:
        self._orders_path = Path(orders_path)
        self._campaigns_path = Path(campaigns_path)
        self._products_path = Path(products_path)
        self._pending_path = Path(pending_path)

    def evaluate(self) -> list[Action]:
        """Run all evaluations and return recommended actions."""
        orders = self._load_json(self._orders_path)
        campaigns = self._load_json(self._campaigns_path)
        products = self._load_json(self._products_path)
        pending = self._load_json(self._pending_path)

        actions: list[Action] = []

        # Campaign evaluations
        for cam_id, cam in campaigns.items():
            actions.extend(self._evaluate_campaign(cam, orders))

        # Product evaluations
        for key, prod in products.items():
            actions.extend(self._evaluate_product(prod, orders))

        # Pending order confirmations
        actions.extend(self._evaluate_pending_orders(orders))

        # Stock alerts from pending products
        for pid, prod in pending.items():
            if prod.get("stock", 0) < STOCK_ALERT_THRESHOLD:
                actions.append(Action(
                    action_type=ActionType.ALERT_STOCK,
                    priority=ActionPriority.MEDIUM,
                    product_id=pid,
                    product_name=prod.get("name"),
                    reason=f"Stock {prod.get('stock', 0)} unidades — por debajo del umbral de alerta ({STOCK_ALERT_THRESHOLD})",
                    data={"stock": prod.get("stock", 0)},
                ))

        # Sort by priority
        priority_order = {ActionPriority.CRITICAL: 0, ActionPriority.HIGH: 1, ActionPriority.MEDIUM: 2, ActionPriority.LOW: 3}
        actions.sort(key=lambda a: priority_order.get(a.priority, 99))

        logger.info(f"[DecisionEngine] Generated {len(actions)} actions")
        return actions

    def _evaluate_campaign(self, cam: dict, orders: dict) -> list[Action]:
        """Evaluate a single campaign."""
        actions = []
        if cam.get("status") != "ACTIVE":
            return actions

        total_spend = cam.get("total_spend_usd", 0)
        conversions = cam.get("conversions", 0)
        clicks = cam.get("clicks", 0)
        impressions = cam.get("impressions", 0)
        spend_log = cam.get("spend_log", [])
        days_active = len(spend_log)
        product_id = cam.get("product_id", "")
        product_name = cam.get("product_name", product_id)

        # CPA check
        if conversions > 0 and total_spend > 0:
            real_cpa = total_spend / conversions
            if real_cpa > CPA_TARGET_USD and days_active >= PAUSE_DAYS_MIN:
                actions.append(Action(
                    action_type=ActionType.PAUSE_CAMPAIGN,
                    priority=ActionPriority.CRITICAL,
                    product_id=product_id,
                    product_name=product_name,
                    campaign_id=cam.get("id"),
                    reason=f"CPA real ${real_cpa:.2f} supera objetivo ${CPA_TARGET_USD} por {days_active} dias",
                    data={"real_cpa": real_cpa, "target_cpa": CPA_TARGET_USD, "days": days_active},
                ))

        # Zero conversions after spend
        if total_spend >= 15 and conversions == 0:
            actions.append(Action(
                action_type=ActionType.PAUSE_CAMPAIGN,
                priority=ActionPriority.HIGH,
                product_id=product_id,
                product_name=product_name,
                campaign_id=cam.get("id"),
                reason=f"${total_spend:.2f} gastados sin ninguna conversion",
                data={"spend": total_spend, "conversions": 0},
            ))

        # ROAS check for scaling
        if total_spend > 0 and conversions > 0:
            # Calculate revenue from delivered orders for this product
            prod_orders = [o for o in orders.values() if o.get("product_id") == product_id and o.get("status") == "DELIVERED"]
            revenue = sum(o.get("product_price", 0) for o in prod_orders)
            if revenue > 0:
                roas = revenue / total_spend
                if roas >= SCALE_ROAS_THRESHOLD and days_active >= SCALE_DAYS_MIN:
                    actions.append(Action(
                        action_type=ActionType.SCALE_BUDGET,
                        priority=ActionPriority.HIGH,
                        product_id=product_id,
                        product_name=product_name,
                        campaign_id=cam.get("id"),
                        reason=f"ROAS {roas:.1f}x supera umbral {SCALE_ROAS_THRESHOLD}x por {days_active} dias. Escalar budget",
                        data={"roas": roas, "revenue": revenue, "spend": total_spend},
                    ))

        # CTR check — creative fatigue
        if impressions >= 1000 and clicks > 0:
            ctr = clicks / impressions * 100
            if ctr < 0.5:
                actions.append(Action(
                    action_type=ActionType.REFRESH_CREATIVE,
                    priority=ActionPriority.MEDIUM,
                    product_id=product_id,
                    product_name=product_name,
                    campaign_id=cam.get("id"),
                    reason=f"CTR {ctr:.2f}% muy bajo. El creativo puede estar agotado",
                    data={"ctr": ctr, "impressions": impressions, "clicks": clicks},
                ))

        return actions

    def _evaluate_product(self, prod: dict, orders: dict) -> list[Action]:
        """Evaluate a published product."""
        actions = []
        product_id = str(prod.get("id", ""))
        product_name = prod.get("name", "")

        # Delivery rate check
        prod_orders = [o for o in orders.values() if o.get("product_id") == product_id]
        delivered = [o for o in prod_orders if o.get("status") == "DELIVERED"]
        rejected = [o for o in prod_orders if o.get("status") == "REJECTED"]
        completed = len(delivered) + len(rejected)

        if completed >= 5:
            delivery_rate = len(delivered) / completed
            if delivery_rate < (1 - ESTIMATED_REJECTION_RATE - 0.10):  # 10% worse than estimated
                actions.append(Action(
                    action_type=ActionType.REJECT_PRODUCT,
                    priority=ActionPriority.CRITICAL,
                    product_id=product_id,
                    product_name=product_name,
                    reason=f"Tasa de entrega {delivery_rate:.0%} ({len(delivered)}/{completed}) muy baja. Considerar retirar",
                    data={"delivery_rate": delivery_rate, "delivered": len(delivered), "rejected": len(rejected)},
                ))

        # Stock check
        stock = prod.get("stock", 0)
        if stock < MIN_STOCK_FOR_BUY and stock > 0:
            actions.append(Action(
                action_type=ActionType.ALERT_STOCK,
                priority=ActionPriority.HIGH,
                product_id=product_id,
                product_name=product_name,
                reason=f"Stock bajo: {stock} unidades. Pausar ads si no hay restock",
                data={"stock": stock},
            ))

        # Winner detection
        if completed >= 10 and len(delivered) >= 8:
            delivery_rate = len(delivered) / completed
            if delivery_rate >= 0.80:
                revenue = sum(o.get("product_price", 0) for o in delivered)
                profit = sum(o.get("product_price", 0) - o.get("product_cost", 0) for o in delivered)
                actions.append(Action(
                    action_type=ActionType.REPLICATE_WINNER,
                    priority=ActionPriority.MEDIUM,
                    product_id=product_id,
                    product_name=product_name,
                    reason=f"WINNER: {delivery_rate:.0%} entrega, ${profit:.0f} profit en {completed} pedidos. Buscar productos similares",
                    data={"delivery_rate": delivery_rate, "revenue": revenue, "profit": profit},
                ))

        return actions

    def _evaluate_pending_orders(self, orders: dict) -> list[Action]:
        """Check for orders that need attention."""
        actions = []
        now = datetime.utcnow()

        pending = [o for o in orders.values() if o.get("status") == "PENDING"]

        for order in pending:
            created = order.get("created_at", "")
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00")).replace(tzinfo=None)
                hours_pending = (now - created_dt).total_seconds() / 3600
                if hours_pending > 2:
                    actions.append(Action(
                        action_type=ActionType.CONFIRM_PENDING,
                        priority=ActionPriority.HIGH if hours_pending > 6 else ActionPriority.MEDIUM,
                        product_id=order.get("product_id"),
                        product_name=order.get("product_name"),
                        reason=f"Pedido #{order.get('id', '?')} de {order.get('customer_name', '?')} lleva {hours_pending:.0f}h sin confirmar",
                        data={"order_id": order.get("id"), "customer": order.get("customer_name"), "hours": round(hours_pending, 1)},
                    ))
            except (ValueError, TypeError):
                pass

        return actions

    @staticmethod
    def _load_json(path: Path) -> dict:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
