"""
Auth service — JWT issuance, local account verification, RBAC roles.
Server-side counterpart to the dashboard login. Production-grade primitives:
Argon2id hashing, short-lived JWTs. SSO (Entra/Okta) handled in oidc.py.
"""
from __future__ import annotations
import datetime as dt
from jose import jwt, JWTError
from passlib.context import CryptContext

from ..config import get_settings

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Roles → permissions (mirrors LLD §9 RBAC matrix)
ROLE_PERMISSIONS = {
    "admin":          {"views": "all", "can_approve": True,  "admin": True},
    "senior_analyst": {"views": "all", "can_approve": True,  "admin": False},
    "analyst":        {"views": ["overview", "alerts", "threat", "remediator"], "can_approve": False, "admin": False},
    "executive":      {"views": ["overview", "compliance", "remediator"], "can_approve": False, "admin": False},
    "read_only":      {"views": "all", "can_approve": False, "admin": False},
}

# Demo local accounts (Argon2id-hashed at startup). In production these live in the users table.
_DEMO_USERS = {
    "admin":   {"role": "admin",          "display": "Sam Okonkwo",   "email": "admin@secureglass.io",   "password": "demo"},
    "analyst": {"role": "senior_analyst", "display": "Nadia Rahman",  "email": "n.rahman@secureglass.io","password": "demo"},
    "exec":    {"role": "executive",      "display": "Chris Vance",   "email": "ciso@secureglass.io",    "password": "demo"},
    "auditor": {"role": "read_only",      "display": "Pat Lindqvist", "email": "audit@secureglass.io",   "password": "demo"},
}
_HASHED = {u: {**v, "password_hash": pwd_context.hash(v["password"])} for u, v in _DEMO_USERS.items()}


def verify_local(username: str, password: str) -> dict | None:
    user = _HASHED.get(username.lower())
    if not user:
        return None
    if not pwd_context.verify(password, user["password_hash"]):
        return None
    return {"username": username.lower(), "role": user["role"],
            "display": user["display"], "email": user["email"]}


def create_access_token(sub: str, role: str, extra: dict | None = None) -> str:
    s = get_settings()
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": sub, "role": role,
        "iat": now, "exp": now + dt.timedelta(minutes=s.jwt_access_ttl_minutes),
        **(extra or {}),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm="HS256")


def decode_token(token: str) -> dict | None:
    s = get_settings()
    try:
        return jwt.decode(token, s.jwt_secret, algorithms=["HS256"])
    except JWTError:
        return None


def role_permissions(role: str) -> dict:
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["read_only"])
