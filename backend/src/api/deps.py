"""FastAPI dependencies — extract and validate the current user from JWT."""
from __future__ import annotations
from fastapi import Header, HTTPException
from ..auth.service import decode_token, role_permissions


async def current_user(authorization: str | None = Header(default=None)) -> dict:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {
        "username": payload.get("sub"),
        "role": payload.get("role"),
        "permissions": role_permissions(payload.get("role", "read_only")),
    }


def require_approver(user: dict) -> dict:
    if not user["permissions"].get("can_approve"):
        raise HTTPException(status_code=403, detail="Role cannot approve remediations")
    return user
