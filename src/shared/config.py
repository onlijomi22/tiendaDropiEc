"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables or .env file.
Never hardcode secrets — always use this module.
"""

from functools import lru_cache
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DropiSettings(BaseSettings):
    """Dropi platform credentials."""

    email: str = Field(description="Dropi account email")
    password: SecretStr = Field(description="Dropi account password")
    base_url: str = Field(default="https://app.dropi.ec", description="Dropi app URL")

    model_config = SettingsConfigDict(env_prefix="DROPI_", env_file=".env", extra="ignore")


class GeminiSettings(BaseSettings):
    """Google Gemini AI configuration."""

    api_key: SecretStr = Field(description="Gemini API key")
    model: str = Field(default="gemini-3.1-pro-preview", description="Model to use")

    model_config = SettingsConfigDict(env_prefix="GEMINI_", env_file=".env", extra="ignore")


class GoogleAdsSettings(BaseSettings):
    """Google Ads API credentials."""

    developer_token: SecretStr = Field(description="Google Ads developer token")
    client_id: str = Field(description="OAuth2 client ID")
    client_secret: SecretStr = Field(description="OAuth2 client secret")
    refresh_token: SecretStr = Field(description="OAuth2 refresh token")
    customer_id: str = Field(description="Google Ads customer ID")

    model_config = SettingsConfigDict(env_prefix="GOOGLE_ADS_", env_file=".env", extra="ignore")


class TikTokAdsSettings(BaseSettings):
    """TikTok Ads API credentials."""

    app_id: str = Field(description="TikTok app ID")
    secret: SecretStr = Field(description="TikTok app secret")
    access_token: SecretStr = Field(description="TikTok access token")
    advertiser_id: str = Field(description="TikTok advertiser ID")

    model_config = SettingsConfigDict(env_prefix="TIKTOK_", env_file=".env", extra="ignore")


class WhatsAppSettings(BaseSettings):
    """Meta WhatsApp Business Cloud API credentials."""

    access_token: SecretStr = Field(description="Meta permanent access token")
    phone_number_id: str = Field(description="WhatsApp phone number ID")
    business_account_id: str = Field(description="WhatsApp Business Account ID")
    verify_token: str = Field(description="Webhook verify token")

    model_config = SettingsConfigDict(env_prefix="WHATSAPP_", env_file=".env", extra="ignore")


class SchedulerSettings(BaseSettings):
    """APScheduler cron expressions per agent."""

    products_cron: str = Field(default="0 */6 * * *")
    ads_cron: str = Field(default="0 */12 * * *")
    analytics_cron: str = Field(default="0 8 * * *")

    model_config = SettingsConfigDict(env_prefix="SCHEDULER_", env_file=".env", extra="ignore")


class AppSettings(BaseSettings):
    """Top-level application settings."""

    log_level: str = Field(default="INFO")
    log_file: str = Field(default="logs/tienda_dropi.log")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache(maxsize=1)
def get_dropi_settings() -> DropiSettings:
    """Return cached Dropi settings (loaded once)."""
    return DropiSettings()


@lru_cache(maxsize=1)
def get_gemini_settings() -> GeminiSettings:
    """Return cached Gemini settings."""
    return GeminiSettings()


@lru_cache(maxsize=1)
def get_google_ads_settings() -> GoogleAdsSettings:
    """Return cached Google Ads settings."""
    return GoogleAdsSettings()


@lru_cache(maxsize=1)
def get_tiktok_settings() -> TikTokAdsSettings:
    """Return cached TikTok Ads settings."""
    return TikTokAdsSettings()


@lru_cache(maxsize=1)
def get_whatsapp_settings() -> WhatsAppSettings:
    """Return cached WhatsApp settings."""
    return WhatsAppSettings()


@lru_cache(maxsize=1)
def get_scheduler_settings() -> SchedulerSettings:
    """Return cached Scheduler settings."""
    return SchedulerSettings()


@lru_cache(maxsize=1)
def get_app_settings() -> AppSettings:
    """Return cached app-level settings."""
    return AppSettings()
