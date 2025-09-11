import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy import create_engine, text


DB_URL = os.getenv("DATABASE_URL", "postgresql+psycopg2://app:app@localhost:5432/app")
engine = create_engine(DB_URL, future=True)


def seed_core(conn):
    # Tenants and orgs
    tenant = str(uuid4())
    civil = str(uuid4())
    maint = str(uuid4())
    tech = str(uuid4())
    conn.execute(text("insert into organizations (id, tenant_id, name, type) values (:id,:t,'Civil Org','Civil')"), {"id": civil, "t": tenant})
    conn.execute(text("insert into organizations (id, tenant_id, name, type) values (:id,:t,'Maintenance Org','Maintenance')"), {"id": maint, "t": tenant})
    conn.execute(text("insert into organizations (id, tenant_id, name, type) values (:id,:t,'Technical Org','Technical')"), {"id": tech, "t": tenant})

    # SMME
    smme = str(uuid4())
    conn.execute(text("insert into smmes (id) values (:id)"), {"id": smme})

    # PONs with default center/radius and optional geofence poly
    pons = [str(uuid4()) for _ in range(5)]
    for pid in pons:
        conn.execute(text("insert into pons (id, status, center_lat, center_lng, geofence_radius_m) values (:id,'planned', -28.595, 24.005, 250)"), {"id": pid})

    # Contracts with SLAs
    conn.execute(text("insert into contracts (id, org_id, scope_type, sla_p1_min, sla_p2_min, sla_p3_min, sla_p4_min, active, valid_from) values (gen_random_uuid(), :o, 'Technical', 120, 240, 480, 1440, true, current_date)"), {"o": tech})
    conn.execute(text("insert into contracts (id, org_id, scope_type, sla_p1_min, sla_p2_min, sla_p3_min, sla_p4_min, active, valid_from) values (gen_random_uuid(), :o, 'Maintenance', 120, 240, 480, 1440, true, current_date)"), {"o": maint})
    conn.execute(text("insert into contracts (id, org_id, scope_type, sla_p1_min, sla_p2_min, sla_p3_min, sla_p4_min, active, valid_from) values (gen_random_uuid(), :o, 'Civil', 0, 0, 0, 0, true, current_date)"), {"o": civil})

    # Assignments by step and PON
    for pid in pons:
        conn.execute(text("insert into assignments (id, org_id, pon_id, step_type) values (gen_random_uuid(), :o, :p, 'Technical')"), {"o": tech, "p": pid})
        conn.execute(text("insert into assignments (id, org_id, pon_id, step_type) values (gen_random_uuid(), :o, :p, 'Maintenance')"), {"o": maint, "p": pid})

    # Devices: one OLT and two ONUs per PON
    for pid in pons:
        olt_id = str(uuid4())
        conn.execute(text("insert into devices (id, pon_id, name, role, vendor, model, status, created_at) values (:id, :p, :n, 'OLT', 'VendorX', 'X-OLT', 'Active', now())"), {"id": olt_id, "p": pid, "n": f"OLT-{pid[:6]}"})
        for i in range(1, 3):
            conn.execute(text("insert into devices (id, pon_id, name, role, vendor, model, status, created_at) values (gen_random_uuid(), :p, :n, 'ONT', 'VendorX', 'X-ONT', 'Active', now())"), {"p": pid, "n": f"ONT-{pid[:4]}-{i}"})

    # Tasks scaffold for gates
    for pid in pons:
        conn.execute(text("insert into tasks (id, pon_id, step, status) values (gen_random_uuid(), :p, 'CAC', 'Pending')"), {"p": pid})
        conn.execute(text("insert into tasks (id, pon_id, step, status) values (gen_random_uuid(), :p, 'PolePlanting', 'Pending')"), {"p": pid})
        conn.execute(text("insert into tasks (id, pon_id, step, status) values (gen_random_uuid(), :p, 'Stringing', 'Pending')"), {"p": pid})

    # Rate card for SMME
    conn.execute(text("insert into rate_cards (id, smme_id, step, unit, rate_cents, active, valid_from) values (gen_random_uuid(), :s, 'PolePlanting', 'per_pole', 50000, true, current_date)"), {"s": smme})
    conn.execute(text("insert into rate_cards (id, smme_id, step, unit, rate_cents, active, valid_from) values (gen_random_uuid(), :s, 'Stringing', 'per_meter', 150, true, current_date)"), {"s": smme})
    conn.execute(text("insert into rate_cards (id, smme_id, step, unit, rate_cents, active, valid_from) values (gen_random_uuid(), :s, 'CAC', 'per_check', 25000, true, current_date)"), {"s": smme})

    return {"tenant": tenant, "orgs": {"civil": civil, "maintenance": maint, "technical": tech}, "smme": smme, "pons": pons}


def main():
    with engine.begin() as conn:
        info = seed_core(conn)
        print("Seeded:")
        print(info)


if __name__ == "__main__":
    main()

