from __future__ import annotations

from uuid import uuid4
from sqlalchemy import text

from app.core.deps import SessionLocal


ROLES = ["ADMIN", "PM", "SITE", "SMME"]


def run():
    db = SessionLocal()
    try:
        # Seed roles
        for r in ROLES:
            db.execute(text("insert into roles (id, name) values (gen_random_uuid(), :n) on conflict (name) do nothing"), {"n": r})
        # Seed users (3 per role)
        for r in ROLES:
            for i in range(1, 4):
                email = f"demo_{r.lower()}{i}@example.com"
                db.execute(
                    text(
                        "insert into users (id, email, role) values (gen_random_uuid(), :e, :r) on conflict (email) do nothing"
                    ),
                    {"e": email, "r": r},
                )
        # Seed two wards, five PONs
        wards = ["Ward1", "Ward2"]
        for w in wards:
            db.execute(text("insert into wards (id, name) values (gen_random_uuid(), :n) on conflict do nothing"), {"n": w})
        for i in range(1, 6):
            db.execute(
                text(
                    "insert into pons (id, status, geofence_radius_m) values (gen_random_uuid(), 'New', 200) on conflict do nothing"
                )
            )
        # Seed three SMMEs
        for i in range(1, 4):
            db.execute(text("insert into smmes (id) values (gen_random_uuid())"))
        # Seed base stock/assets
        for i in range(20):
            code = str(uuid4()).split("-")[0].upper()
            db.execute(
                text(
                    "insert into assets (id, type, code, status) values (gen_random_uuid(), 'POLE', :c, 'In Store') on conflict do nothing"
                ),
                {"c": code},
            )
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    run()

