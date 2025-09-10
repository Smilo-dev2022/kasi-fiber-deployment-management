from typing import Optional
from uuid import UUID


class User:
    def __init__(self, org_id: Optional[UUID] = None):
        self.org_id = org_id

