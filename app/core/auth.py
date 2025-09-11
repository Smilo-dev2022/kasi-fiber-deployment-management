import os
from typing import Any, Dict, Optional

import jwt
from fastapi import HTTPException


def get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="Server not configured: JWT_SECRET is missing")
    return secret


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

