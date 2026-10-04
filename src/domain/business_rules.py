"""Centralized business rules for TiendaDropiEc.

All business constants, thresholds, and configurable rules live here.
No other file should define these values locally.

References:
- specs/products/product.spec.md (CA-PROD-01, CA-PROD-02, CA-PROD-03)
- specs/ads/campaign.spec.md (CA-ADS-01, CA-ADS-02, CA-ADS-03)
- specs/analytics/report.spec.md (CA-ANAL-01, CA-ANAL-02)
- specs/customer/conversation.spec.md (CA-CUST-02, CA-CUST-03)
- DECISIONS.md (ADR-002, ADR-006, ADR-010)
"""

# --- Product Scoring ---
MIN_MARGIN_PCT: float = 25.0            # CA-PROD-01: < 25% = SKIP inmediato
TARGET_MARGIN_PCT: float = 35.0         # Margen objetivo para considerar "viable"
SCORE_BUY_THRESHOLD: float = 70.0       # CA-PROD-02: >= 70 = BUY
SCORE_WATCH_THRESHOLD: float = 40.0     # CA-PROD-02: 40-69 = WATCH, < 40 = SKIP
MIN_STOCK_FOR_BUY: int = 10             # CA-PROD-03: stock < 10 = no BUY
STOCK_ALERT_THRESHOLD: int = 5          # Alerta temprana de stock bajo
MAX_PRODUCTS_PER_RUN: int = 50

# --- Scoring Weights (must sum to 100) ---
MARGIN_WEIGHT: int = 40
TREND_WEIGHT: int = 30
COMPETITION_WEIGHT: int = 30
DEFAULT_TREND_SCORE: float = 0.5        # Placeholder hasta tener datos reales

# --- Pricing ---
ESTIMATED_SHIPPING_COST_USD: float = 6.00   # Servientrega EC estimado
ESTIMATED_CPA_USD: float = 8.00             # Costo estimado por adquisicion
TARGET_PROFIT_USD: float = 8.00             # Ganancia objetivo por venta (markup)

# --- Competition Thresholds ---
COMPETITION_LOW_MAX_SELLERS: int = 5        # < 5 vendedores = LOW
COMPETITION_HIGH_MIN_SELLERS: int = 20      # > 20 vendedores = HIGH

# --- Ads ---
INITIAL_DAILY_BUDGET_USD: float = 5.0       # CA-ADS-03: fase testing
SCALE_BUDGET_USD: float = 15.0              # CA-ADS-03: fase escalado
PAUSE_ROAS_THRESHOLD: float = 2.0           # CA-ADS-02: ROAS < 2.0 por 3 dias = pausar
SCALE_ROAS_THRESHOLD: float = 3.0           # CA-ADS-03: ROAS > 3.0 por 5 dias = escalar
TARGET_ROAS: float = 3.0
ROAS_ALERT_THRESHOLD: float = 1.5           # Alerta temprana (analytics)
PAUSE_DAYS_MIN: int = 3
SCALE_DAYS_MIN: int = 5
CPA_TARGET_USD: float = 8.0

# --- Ads Copy Limits ---
GOOGLE_HEADLINE_MAX_CHARS: int = 30         # CA-ADS-01
GOOGLE_DESCRIPTION_MAX_CHARS: int = 90      # CA-ADS-01

# --- Customer ---
MAX_AGENT_ATTEMPTS: int = 3                 # CA-CUST-02
CONTEXT_WINDOW_MESSAGES: int = 10           # CA-CUST-03

# --- Order / Delivery ---
ESTIMATED_REJECTION_RATE: float = 0.20      # 20% de envios rechazados en puerta (COD Ecuador)
ESTIMATED_RETURN_RATE: float = 0.05         # 5% de devoluciones post-entrega
CONFIRMATION_TIMEOUT_HOURS: int = 24        # Horas para confirmar antes de cancelar

# --- Analytics ---
ANOMALY_DROP_THRESHOLD_PCT: float = 30.0    # CA-ANAL-02
