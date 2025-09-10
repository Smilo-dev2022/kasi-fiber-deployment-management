from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from passlib.context import CryptContext

from ..settings import settings
from ..models.user import User
from ..models.smme import SMME
from ..models.pon import PON
from ..models.cac import CACCheck
from ..models.stringing import StringingRun
from ..models.stock import StockItem
from ..models.invoice import Invoice


pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")


def main():
    engine = create_engine(settings.database_url, future=True)
    with Session(engine) as db:
        # Users
        def add_user(name: str, email: str, role: str):
            user = db.query(User).filter_by(email=email).first()
            if user:
                return user
            u = User(
                name=name,
                email=email,
                role=role,
                phone=None,
                hashed_password=pwd.hash("password"),
                created_at=datetime.utcnow(),
            )
            db.add(u)
            db.commit()
            db.refresh(u)
            return u

        admin = add_user("Admin", "admin@fibertime.local", "ADMIN")
        pm = add_user("PM", "pm@fibertime.local", "PM")
        site = add_user("Site", "site@fibertime.local", "SITE")
        smme_user = add_user("SMME", "smme@fibertime.local", "SMME")
        auditor = add_user("Auditor", "auditor@fibertime.local", "AUDITOR")

        # SMMEs
        smmes = []
        for i in range(1, 4):
            name = f"SMME {i}"
            smme = db.query(SMME).filter_by(name=name).first()
            if not smme:
                smme = SMME(name=name, contact_name=f"Contact {i}", contact_phone=f"+27 000 000{i}")
                db.add(smme)
                db.commit()
                db.refresh(smme)
            smmes.append(smme)

        # PONs with two wards and five entries
        ward_names = ["Ward 1", "Ward 2"]
        pon_ids = []
        for idx in range(1, 6):
            pon_num = f"PON-{1000+idx}"
            pon = db.query(PON).filter_by(pon_number=pon_num).first()
            if not pon:
                pon = PON(
                    pon_number=pon_num,
                    ward=ward_names[idx % 2],
                    street_area=f"Street {idx}",
                    homes_passed=50 + idx,
                    poles_planned=10,
                    poles_planted=5 if idx % 2 == 0 else 0,
                    smme_id=smmes[idx % len(smmes)].id,
                    created_by=admin.id,
                    created_at=datetime.utcnow(),
                )
                db.add(pon)
                db.commit()
                db.refresh(pon)
            pon_ids.append(pon.id)

        # Stock
        def seed_item(sku: str, name: str, unit: str, on_hand: float):
            item = db.query(StockItem).filter_by(sku=sku).first()
            if not item:
                item = StockItem(sku=sku, name=name, unit=unit, on_hand=on_hand)
                db.add(item)
                db.commit()
        seed_item("POLE7.5", "Pole 7.5m", "ea", 100)
        seed_item("DEADEND", "Dead End", "ea", 200)
        seed_item("BRACKET", "Bracket", "ea", 500)
        seed_item("DRUM24C", "24C Drum", "drum", 5)

        # CAC checks: one pass and one fail
        pon_first = db.get(PON, pon_ids[0])
        if pon_first:
            if not db.query(CACCheck).filter_by(pon_id=pon_first.id).first():
                db.add(CACCheck(
                    pon_id=pon_first.id,
                    pole_number="1",
                    pole_length_m=7.5,
                    depth_m=1.15,
                    tag_height_m=2.25,
                    passed=True,
                    checked_by=pm.id,
                    comments="OK",
                    checked_at=datetime.utcnow(),
                ))
                db.add(CACCheck(
                    pon_id=pon_first.id,
                    pole_number="2",
                    pole_length_m=7.6,
                    depth_m=1.0,
                    tag_height_m=2.0,
                    passed=False,
                    checked_by=pm.id,
                    comments="Too shallow",
                    checked_at=datetime.utcnow(),
                ))
                db.commit()

        # Stringing sample
        pon_second = db.get(PON, pon_ids[1])
        if pon_second and not db.query(StringingRun).filter_by(pon_id=pon_second.id).first():
            db.add(StringingRun(pon_id=pon_second.id, meters=120, brackets=30, dead_ends=6, tensioner=2, completed_by=site.id, completed_at=datetime.utcnow()))
            db.commit()

        # One draft invoice
        inv = db.query(Invoice).first()
        if not inv:
            inv = Invoice(pon_id=pon_ids[0], smme_id=smmes[0].id, amount_cents=100000, status="Draft")
            db.add(inv)
            db.commit()

    print("Seed complete. Demo users created with password 'password'.")


if __name__ == "__main__":
    main()

