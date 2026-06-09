"""
SecureGlass — Configuration
Loads all settings from environment variables (.env). Nothing is hardcoded;
secrets stay server-side and are never sent to the browser.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Core ---
    app_name: str = "SecureGlass API"
    environment: str = "development"
    cors_origins: str = "*"  # comma-separated in prod

    # --- Database / cache ---
    postgres_url: str = "postgresql+asyncpg://secureglass:secureglass@localhost:5432/secureglass"
    redis_url: str = "redis://localhost:6379"

    # --- Anthropic ---
    anthropic_api_key: str | None = None

    # --- CrowdStrike Falcon ---
    crowdstrike_client_id: str | None = None
    crowdstrike_client_secret: str | None = None
    crowdstrike_base_url: str = "https://api.crowdstrike.com"

    # --- Mimecast ---
    mimecast_client_id: str | None = None
    mimecast_client_secret: str | None = None
    mimecast_base_url: str = "https://api.services.mimecast.com"

    # --- Qualys VMDR ---
    qualys_username: str | None = None
    qualys_password: str | None = None
    qualys_api_url: str = "https://qualysapi.qg1.apps.qualys.eu"

    # --- Auth / JWT ---
    jwt_secret: str = "change-me-in-production"
    jwt_access_ttl_minutes: int = 15
    jwt_refresh_ttl_days: int = 7

    auth_local_enabled: bool = True
    auth_entra_enabled: bool = False
    auth_okta_enabled: bool = False

    entra_tenant_id: str | None = None
    entra_client_id: str | None = None
    entra_client_secret: str | None = None
    entra_redirect_uri: str | None = None

    okta_issuer: str | None = None
    okta_client_id: str | None = None
    okta_client_secret: str | None = None
    okta_redirect_uri: str | None = None

    # --- Ingestion ---
    ingest_interval_seconds: int = 300  # 5 min default poll

    def connector_status(self) -> dict[str, bool]:
        """Report which connectors have credentials configured."""
        return {
            "crowdstrike": bool(self.crowdstrike_client_id and self.crowdstrike_client_secret),
            "mimecast": bool(self.mimecast_client_id and self.mimecast_client_secret),
            "qualys": bool(self.qualys_username and self.qualys_password),
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
