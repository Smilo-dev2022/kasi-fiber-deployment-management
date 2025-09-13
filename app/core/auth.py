import os
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException


def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="Server not configured: JWT_SECRET is missing")
    return secret


def _decode_with_legacy_fallback(token: str) -> Optional[Dict[str, Any]]:
    primary = get_jwt_secret()
    legacy_raw = os.getenv("JWT_SECRET_LEGACY")

    # Try primary first
    try:
        return jwt.decode(token, primary, algorithms=["HS256"])
    except Exception:
        pass

    if not legacy_raw:
        return None

    # Try legacy as-is
    try:
        return jwt.decode(token, legacy_raw, algorithms=["HS256"])
    except Exception:
        pass

    # Try legacy as base64-decoded bytes -> utf-8 string
    try:
        import base64

        maybe_b64 = base64.b64decode(legacy_raw)
        try:
            legacy_decoded = maybe_b64.decode("utf-8")
        except Exception:
            # If it is binary, use bytes directly
            legacy_decoded = maybe_b64
        return jwt.decode(token, legacy_decoded, algorithms=["HS256"])
    except Exception:
        return None


def decode_bearer_token(authorization_header: Optional[str]) -> Optional[Dict[str, Any]]:
    if not authorization_header:
        return None
    parts = authorization_header.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1]
    payload = _decode_with_legacy_fallback(token)
    if payload is None:
        # Invalid token; treat as anonymous
        return None
    return payload


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

