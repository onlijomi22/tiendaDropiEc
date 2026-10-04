"""Domain-specific exceptions for TiendaDropiEc.

All exceptions follow Clean Architecture: domain exceptions are independent
of infrastructure details. Infrastructure layers catch low-level errors and
raise these domain exceptions instead.
"""


class TiendaDropiError(Exception):
    """Base exception for all TiendaDropiEc errors."""


class DomainValidationError(TiendaDropiError):
    """Raised when a domain entity fails validation rules."""


class ProductNotFoundError(TiendaDropiError):
    """Raised when a product cannot be found in the Dropi catalog."""

    def __init__(self, product_id: str) -> None:
        super().__init__(f"Product '{product_id}' not found in Dropi catalog.")
        self.product_id = product_id


class DropiAuthError(TiendaDropiError):
    """Raised when Dropi authentication fails."""


class DropiScrapingError(TiendaDropiError):
    """Raised when Playwright scraping fails or Dropi UI changes."""


class AdsAPIError(TiendaDropiError):
    """Raised when Google Ads or TikTok Ads API calls fail."""

    def __init__(self, platform: str, message: str) -> None:
        super().__init__(f"[{platform}] Ads API error: {message}")
        self.platform = platform


class WhatsAppAPIError(TiendaDropiError):
    """Raised when Meta WhatsApp Cloud API calls fail."""


class AgentExecutionError(TiendaDropiError):
    """Raised when a Gemini agent fails during its ReAct loop."""

    def __init__(self, agent_name: str, reason: str) -> None:
        super().__init__(f"Agent '{agent_name}' failed: {reason}")
        self.agent_name = agent_name


class SpecViolationError(TiendaDropiError):
    """Raised when runtime data violates a domain spec constraint.

    This is the SDD enforcement exception. Use this when a spec rule
    (from specs/*.spec.md) is violated at runtime.
    """

    def __init__(self, spec_id: str, message: str) -> None:
        super().__init__(f"[Spec {spec_id}] {message}")
        self.spec_id = spec_id
