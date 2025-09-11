import os
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException


def _is_truthy(value: Optional[str]) -> bool:
    if not value:
        return False
    normalized = value.strip().lower()
    return normalized in {"1", "true", "yes", "y"}


def _looks_like_base64(value: str) -> bool:
    if not value:
        return False
    # Heuristic similar to Node side
    import re
    if len(value) % 4 != 0:
        return False
    return re.fullmatch(r"[A-Za-z0-9+/]+={0,2}", value) is not None


def get_jwt_secret() -> bytes:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="Server not configured: JWT_SECRET is missing")

    encoding = (os.getenv("JWT_SECRET_ENCODING") or "").strip().lower()
    is_base64_flag = _is_truthy(os.getenv("JWT_SECRET_BASE64"))
    should_decode_base64 = is_base64_flag or encoding == "base64" or _looks_like_base64(secret)

    if should_decode_base64:
        try:
            import base64
            return base64.b64decode(secret)
        except Exception as exc:
            raise HTTPException(status_code=500, detail="Invalid base64 JWT secret provided") from exc
    return secret.encode("utf-8")


def decode_bearer_token(authorization_header: Optional[str]) -> Optional[Dict[str, Any]]:
    if not authorization_header:
        return None
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1]
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
        return payload
    except Exception:
        # Invalid token; treat as anonymous
        return None


def extract_role_from_claims(claims: Dict[str, Any]) -> Optional[str]:
    if not claims:
        return None
    # Prefer explicit role claim if present
    role = claims.get("role") or claims.get("user_role")
    # Supabase JWT may carry roles in app_metadata
    if not role:
        app_meta = claims.get("app_metadata") or {}
        role = app_meta.get("role")
    # Default to 'authenticated' when a token exists but no role claim
    return role or "authenticated"

