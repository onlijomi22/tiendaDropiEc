"""Order domain entities for COD (Cash on Delivery) dropshipping."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class OrderStatus(str, Enum):
    """Order lifecycle for COD dropshipping."""
    PENDING = "PENDING"            # Formulario enviado, sin confirmar
    CONFIRMED = "CONFIRMED"        # Cliente confirmó por WhatsApp
    SENT_TO_DROPI = "SENT_TO_DROPI"  # Pedido creado en Dropi
    SHIPPED = "SHIPPED"            # Despachado por courier
    DELIVERED = "DELIVERED"        # Entregado y cobrado
    REJECTED = "REJECTED"          # Rechazado en puerta
    CANCELLED = "CANCELLED"        # Cancelado antes de envío
    RETURNED = "RETURNED"          # Devuelto post-entrega


class Order(BaseModel):
    """A customer order."""
    id: str = Field(description="Unique order ID")
    product_id: str
    product_name: str
    product_price: float = Field(gt=0)
    product_cost: float = Field(gt=0, description="Dropi cost")

    # Customer
    customer_name: str = Field(min_length=1)
    customer_phone: str = Field(min_length=7)
    customer_city: str = Field(min_length=1)
    customer_address: str = Field(default="")

    # Status
    status: OrderStatus = OrderStatus.PENDING
    status_history: list[dict] = Field(default_factory=list)

    # Tracking
    dropi_order_id: str | None = None
    tracking_number: str | None = None
    courier: str = "Servientrega"

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    confirmed_at: datetime | None = None
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None

    # Source
    landing_url: str = ""
    utm_source: str = ""
    utm_medium: str = ""
    utm_campaign: str = ""

    @property
    def gross_profit(self) -> float:
        return self.product_price - self.product_cost

    @property
    def margin_pct(self) -> float:
        if self.product_price <= 0:
            return 0.0
        return (self.product_price - self.product_cost) / self.product_price * 100
