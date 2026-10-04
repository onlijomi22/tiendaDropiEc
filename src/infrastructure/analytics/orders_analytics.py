"""Analytics computed from orders.json — no external dependencies.

Reads the flat-file orders database and computes real metrics:
conversion rates, delivery rates, revenue, profit, per-product performance.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.domain.business_rules import (
    ESTIMATED_CPA_USD,
    ESTIMATED_SHIPPING_COST_USD,
    ESTIMATED_REJECTION_RATE,
)
from src.shared.logger import logger


class OrdersAnalytics:
    """Compute analytics from the orders JSON file."""

    def __init__(self, orders_path: str | None = None) -> None:
        self._path = Path(orders_path or "frontend/src/data/orders.json")

    def _load_orders(self) -> list[dict]:
        if not self._path.exists():
            return []
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            return list(data.values())
        except Exception as e:
            logger.warning(f"[Analytics] Failed to read orders: {e}")
            return []

    def summary(self, days: int | None = None) -> dict[str, Any]:
        """Full analytics summary.

        Args:
            days: If set, only include orders from the last N days.

        Returns:
            Dict with all computed metrics.
        """
        orders = self._load_orders()

        if days:
            cutoff = datetime.utcnow() - timedelta(days=days)
            orders = [
                o for o in orders
                if datetime.fromisoformat(o["created_at"].replace("Z", "+00:00")).replace(tzinfo=None) >= cutoff
            ]

        total = len(orders)
        if total == 0:
            return self._empty_summary()

        # Status counts
        by_status: dict[str, int] = {}
        for o in orders:
            s = o.get("status", "UNKNOWN")
            by_status[s] = by_status.get(s, 0) + 1

        pending = by_status.get("PENDING", 0)
        confirmed = by_status.get("CONFIRMED", 0) + by_status.get("SENT_TO_DROPI", 0)
        shipped = by_status.get("SHIPPED", 0)
        delivered = by_status.get("DELIVERED", 0)
        rejected = by_status.get("REJECTED", 0)
        cancelled = by_status.get("CANCELLED", 0)
        returned = by_status.get("RETURNED", 0)

        # Rates
        completed = delivered + rejected
        confirmation_rate = (total - cancelled) / total * 100 if total > 0 else 0
        delivery_rate = delivered / completed * 100 if completed > 0 else 0
        rejection_rate = rejected / completed * 100 if completed > 0 else 0

        # Revenue & profit
        delivered_orders = [o for o in orders if o.get("status") == "DELIVERED"]
        revenue = sum(o.get("product_price", 0) for o in delivered_orders)
        cost_of_goods = sum(o.get("product_cost", 0) for o in delivered_orders)
        gross_profit = revenue - cost_of_goods
        shipping_cost_total = len([o for o in orders if o.get("status") in ("SHIPPED", "DELIVERED", "REJECTED")]) * ESTIMATED_SHIPPING_COST_USD
        net_profit = gross_profit - shipping_cost_total

        avg_order_value = revenue / len(delivered_orders) if delivered_orders else 0
        avg_profit_per_delivered = net_profit / len(delivered_orders) if delivered_orders else 0

        # Per-product breakdown
        product_metrics = self._per_product_metrics(orders)

        # Time metrics
        avg_confirmation_time = self._avg_time_between_statuses(orders, "PENDING", "CONFIRMED")
        avg_delivery_time = self._avg_time_between_statuses(orders, "SHIPPED", "DELIVERED")

        return {
            "period_days": days or "all_time",
            "computed_at": datetime.utcnow().isoformat(),
            "orders": {
                "total": total,
                "by_status": by_status,
                "pending": pending,
                "confirmed": confirmed,
                "shipped": shipped,
                "delivered": delivered,
                "rejected": rejected,
                "cancelled": cancelled,
                "returned": returned,
            },
            "rates": {
                "confirmation_pct": round(confirmation_rate, 1),
                "delivery_pct": round(delivery_rate, 1),
                "rejection_pct": round(rejection_rate, 1),
                "estimated_rejection": ESTIMATED_REJECTION_RATE * 100,
            },
            "financial": {
                "revenue": round(revenue, 2),
                "cost_of_goods": round(cost_of_goods, 2),
                "gross_profit": round(gross_profit, 2),
                "shipping_costs": round(shipping_cost_total, 2),
                "net_profit": round(net_profit, 2),
                "avg_order_value": round(avg_order_value, 2),
                "avg_profit_per_delivered": round(avg_profit_per_delivered, 2),
            },
            "timing": {
                "avg_confirmation_hours": avg_confirmation_time,
                "avg_delivery_hours": avg_delivery_time,
            },
            "products": product_metrics,
        }

    def _per_product_metrics(self, orders: list[dict]) -> list[dict]:
        """Breakdown by product."""
        by_product: dict[str, list[dict]] = {}
        for o in orders:
            pid = o.get("product_id", "unknown")
            by_product.setdefault(pid, []).append(o)

        result = []
        for pid, prod_orders in by_product.items():
            delivered = [o for o in prod_orders if o.get("status") == "DELIVERED"]
            rejected = [o for o in prod_orders if o.get("status") == "REJECTED"]
            revenue = sum(o.get("product_price", 0) for o in delivered)
            cost = sum(o.get("product_cost", 0) for o in delivered)

            result.append({
                "product_id": pid,
                "product_name": prod_orders[0].get("product_name", "?"),
                "total_orders": len(prod_orders),
                "delivered": len(delivered),
                "rejected": len(rejected),
                "delivery_rate_pct": round(len(delivered) / (len(delivered) + len(rejected)) * 100, 1) if (delivered or rejected) else 0,
                "revenue": round(revenue, 2),
                "gross_profit": round(revenue - cost, 2),
            })

        result.sort(key=lambda x: x["total_orders"], reverse=True)
        return result

    def _avg_time_between_statuses(
        self, orders: list[dict], from_status: str, to_status: str
    ) -> float | None:
        """Average hours between two statuses."""
        durations = []
        for o in orders:
            history = o.get("status_history", [])
            from_time = None
            to_time = None
            for h in history:
                if h.get("status") == from_status and from_time is None:
                    from_time = h.get("timestamp")
                if h.get("status") == to_status and to_time is None:
                    to_time = h.get("timestamp")
            if from_time and to_time:
                try:
                    dt_from = datetime.fromisoformat(from_time.replace("Z", "+00:00"))
                    dt_to = datetime.fromisoformat(to_time.replace("Z", "+00:00"))
                    hours = (dt_to - dt_from).total_seconds() / 3600
                    if hours >= 0:
                        durations.append(hours)
                except (ValueError, TypeError):
                    pass
        return round(sum(durations) / len(durations), 1) if durations else None

    def _empty_summary(self) -> dict:
        return {
            "period_days": 0,
            "computed_at": datetime.utcnow().isoformat(),
            "orders": {"total": 0, "by_status": {}, "pending": 0, "confirmed": 0, "shipped": 0, "delivered": 0, "rejected": 0, "cancelled": 0, "returned": 0},
            "rates": {"confirmation_pct": 0, "delivery_pct": 0, "rejection_pct": 0, "estimated_rejection": ESTIMATED_REJECTION_RATE * 100},
            "financial": {"revenue": 0, "cost_of_goods": 0, "gross_profit": 0, "shipping_costs": 0, "net_profit": 0, "avg_order_value": 0, "avg_profit_per_delivered": 0},
            "timing": {"avg_confirmation_hours": None, "avg_delivery_hours": None},
            "products": [],
        }
