import os
from uuid import uuid4
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.deps import SessionLocal


def seed_core(session: Session) -> None:
    # Tenants/clients are implicit via tenant_id columns; seed organizations and SMMEs
    org_tech = str(uuid4())
    org_civil = str(uuid4())
    session.execute(text("insert into organizations (id, name, type) values (:id, :n, :t) on conflict do nothing"), {"id": org_tech, "n": "TechCo", "t": "Technical"})
    session.execute(text("insert into organizations (id, name, type) values (:id, :n, :t) on conflict do nothing"), {"id": org_civil, "n": "CivilsCo", "t": "Civil"})

    # SMME contractor
    smme_id = str(uuid4())
    session.execute(text("insert into smmes (id) values (:id) on conflict do nothing"), {"id": smme_id})

    # Five PONs
    pon_ids = [str(uuid4()) for _ in range(5)]
    for i, pid in enumerate(pon_ids, start=1):
        session.execute(text("insert into pons (id, status, center_lat, center_lng, geofence_radius_m) values (:id, 'Planned', :lat, :lng, 300) on conflict do nothing"), {"id": pid, "lat": -26.2 - i * 0.001, "lng": 28.04 + i * 0.001})

    # Devices per PON
    for i, pid in enumerate(pon_ids, start=1):
        dev_id = str(uuid4())
        session.execute(text("""
            insert into devices (id, pon_id, name, role, vendor, model, serial, mgmt_ip, site, status)
            values (:id, :pon, :name, 'OLT', 'Huawei', 'MA5800', :ser, :ip, :site, 'Active')
            on conflict do nothing
        """), {"id": dev_id, "pon": pid, "name": f"OLT-{i:02d}", "ser": f"SN{i:06d}", "ip": f"10.0.{i}.1", "site": f"PON-{i:02d}"})

    # Contracts and assignments
    session.execute(text("""
        insert into contracts (id, org_id, scope_type, active, valid_from, sla_p1_min, sla_p2_min, sla_p3_min, sla_p4_min)
        values (:id, :org, 'Technical', true, :vf, 60, 240, 1440, 4320)
        on conflict do nothing
    """), {"id": str(uuid4()), "org": org_tech, "vf": date.today()})
    session.execute(text("""
        insert into assignments (id, org_id, step_type)
        values (:id, :org, 'Technical')
        on conflict do nothing
    """), {"id": str(uuid4()), "org": org_tech})

    # Rate cards for SMME (per pole, per meter, per check)
    session.execute(text("""
        insert into rate_cards (id, smme_id, step, unit, rate_cents, active, valid_from)
        values (gen_random_uuid(), :sm, 'PolePlanting', 'per_pole', 150000, true, :vf)
    """), {"sm": smme_id, "vf": date.today()})
    session.execute(text("""
        insert into rate_cards (id, smme_id, step, unit, rate_cents, active, valid_from)
        values (gen_random_uuid(), :sm, 'Stringing', 'per_meter', 250, true, :vf)
    """), {"sm": smme_id, "vf": date.today()})
    session.execute(text("""
        insert into rate_cards (id, smme_id, step, unit, rate_cents, active, valid_from)
        values (gen_random_uuid(), :sm, 'CAC', 'per_check', 50000, true, :vf)
    """), {"sm": smme_id, "vf": date.today()})

    # Stock: one store and starting levels
    store_id = str(uuid4())
    session.execute(text("insert into stores (id, name) values (:id, :n) on conflict do nothing"), {"id": store_id, "n": "Main Store"})
    for sku, qty in (("POLE7.6M", 100), ("BRACKET", 200), ("DRUM1KM", 5)):
        up = session.execute(text("update stock_levels set qty=qty+:q where store_id=:s and sku=:sku"), {"q": qty, "s": store_id, "sku": sku})
        if up.rowcount == 0:
            session.execute(text("insert into stock_levels (store_id, sku, qty) values (:s, :sku, :q)"), {"s": store_id, "sku": sku, "q": qty})


def main():
    with SessionLocal() as session:
        seed_core(session)
        session.commit()
    print("Seed completed")


if __name__ == "__main__":
    main()

