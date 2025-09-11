import os
from typing import Optional

try:
    from supabase import create_client, Client
except Exception:  # pragma: no cover - dependency optional in some envs
    create_client = None
    Client = None  # type: ignore


SUPABASE_URL: str = os.getenv("SUPABASE_URL", "https://bigbujrinohnmoxuidbx.supabase.co")
SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImJpZ2J1anJpbm9obm1veHVpZGJ4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTc1NzkxNTAsImV4cCI6MjA3MzE1NTE1MH0.LnszUQtZO9jCJfr5rSfPqGqYHWok6NjrOSWGh7NbdWw")


_client: Optional[Client] = None  # type: ignore


def get_supabase_client() -> Optional["Client"]:
    global _client
    if _client is None and create_client is not None:
        _client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    return _client

