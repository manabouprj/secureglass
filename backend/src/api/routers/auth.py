"""Auth endpoints — local login + SSO redirect/callback + current user."""
from __future__ import annotations
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from ...auth.service import verify_local, create_access_token, role_permissions
from ...auth.oidc import providers_enabled, authorize_url, exchange_code

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginInput(BaseModel):
    username: str
    password: str


@router.get("/providers")
async def get_providers():
    return providers_enabled()


@router.post("/local/login")
async def local_login(body: LoginInput):
    user = verify_local(body.username, body.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user["username"], user["role"],
                                extra={"display": user["display"], "email": user["email"]})
    return {"access_token": token, "token_type": "bearer",
            "user": user, "permissions": role_permissions(user["role"])}


@router.get("/login/{provider}")
async def sso_login(provider: str):
    try:
        url, state = authorize_url(provider)
    except ValueError:
        raise HTTPException(status_code=404, detail="Unknown provider")
    # In production, persist `state` to validate on callback
    return RedirectResponse(url)


@router.get("/callback/{provider}")
async def sso_callback(provider: str, code: str | None = None):
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code")
    tokens = await exchange_code(provider, code)
    # In production: validate id_token, map IdP groups → role, issue SecureGlass JWT
    return {"provider": provider, "idp_tokens_received": bool(tokens)}
