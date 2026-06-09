"""
OIDC helpers for Microsoft Entra ID (Azure AD) and Okta.
Builds real authorize URLs and exchanges codes for tokens server-side.
The client_secret never leaves the server.
"""
from __future__ import annotations
import secrets
from urllib.parse import urlencode
import httpx

from ..config import get_settings


def providers_enabled() -> dict[str, bool]:
    s = get_settings()
    return {
        "local": s.auth_local_enabled,
        "entra": s.auth_entra_enabled and bool(s.entra_client_id),
        "okta": s.auth_okta_enabled and bool(s.okta_client_id),
    }


def authorize_url(provider: str) -> tuple[str, str]:
    """Return (url, state) for the OIDC authorization redirect."""
    s = get_settings()
    state = secrets.token_urlsafe(24)
    if provider in ("entra", "azuread"):
        base = f"https://login.microsoftonline.com/{s.entra_tenant_id or 'common'}/oauth2/v2.0/authorize"
        params = {
            "client_id": s.entra_client_id or "ENTRA_CLIENT_ID",
            "response_type": "code", "scope": "openid profile email",
            "redirect_uri": s.entra_redirect_uri or "", "state": state,
            "nonce": secrets.token_urlsafe(16),
        }
    elif provider == "okta":
        base = f"{s.okta_issuer or 'https://example.okta.com/oauth2/default'}/v1/authorize"
        params = {
            "client_id": s.okta_client_id or "OKTA_CLIENT_ID",
            "response_type": "code", "scope": "openid profile email",
            "redirect_uri": s.okta_redirect_uri or "", "state": state,
            "nonce": secrets.token_urlsafe(16),
        }
    else:
        raise ValueError(f"Unknown provider {provider}")
    return f"{base}?{urlencode(params)}", state


async def exchange_code(provider: str, code: str) -> dict:
    """Exchange an auth code for tokens (server-side, with client_secret)."""
    s = get_settings()
    if provider in ("entra", "azuread"):
        token_url = f"https://login.microsoftonline.com/{s.entra_tenant_id or 'common'}/oauth2/v2.0/token"
        data = {
            "client_id": s.entra_client_id, "client_secret": s.entra_client_secret,
            "code": code, "grant_type": "authorization_code",
            "redirect_uri": s.entra_redirect_uri,
        }
    else:
        token_url = f"{s.okta_issuer}/v1/token"
        data = {
            "client_id": s.okta_client_id, "client_secret": s.okta_client_secret,
            "code": code, "grant_type": "authorization_code",
            "redirect_uri": s.okta_redirect_uri,
        }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(token_url, data=data)
        resp.raise_for_status()
        return resp.json()
