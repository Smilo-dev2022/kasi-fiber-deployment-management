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


def extract_org_from_claims(claims: Dict[str, Any]) -> Optional[str]:
    """Best-effort extraction of organization id from JWT claims.

    Looks for common keys in both top-level and app_metadata.
    Returns a string UUID or None.
    """
    if not claims:
        return None
    org_id = (
        claims.get("org_id")
        or claims.get("organization_id")
        or claims.get("org")
        or claims.get("organization")
    )
    if not org_id:
        app_meta = claims.get("app_metadata") or {}
        org_id = (
            app_meta.get("org_id")
            or app_meta.get("organization_id")
            or app_meta.get("org")
        )
    return str(org_id) if org_id else None


def extract_tenant_from_claims(claims: Dict[str, Any]) -> Optional[str]:
    """Best-effort extraction of tenant id (client) from JWT claims."""
    if not claims:
        return None
    tenant_id = claims.get("tenant_id") or claims.get("client_id")
    if not tenant_id:
        app_meta = claims.get("app_metadata") or {}
        tenant_id = app_meta.get("tenant_id") or app_meta.get("client_id")
    return str(tenant_id) if tenant_id else None

