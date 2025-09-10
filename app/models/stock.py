from sqlalchemy import Table, MetaData, Column, String as _S, DateTime as _DT, ForeignKey as _FK
from sqlalchemy.dialects.postgresql import UUID as _UUID
from sqlalchemy import insert as _insert


metadata = MetaData()


class Asset:  # Placeholder for ORM class if needed by select queries
    __tablename__ = "assets"


def sa_insert_assets():
    t = Table(
        "assets",
        metadata,
        Column("id", _UUID(as_uuid=True)),
        Column("tenant_id", _UUID(as_uuid=True)),
        Column("type", _S),
        Column("code", _S),
        Column("sku", _S),
        Column("status", _S),
        Column("pon_id", _UUID(as_uuid=True), _FK("pons.id")),
        Column("issued_to", _UUID(as_uuid=True), _FK("users.id")),
        Column("installed_at", _DT(timezone=True)),
        extend_existing=True,
    )
    return _insert(t)

