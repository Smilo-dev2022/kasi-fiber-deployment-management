from sqlalchemy import Table, MetaData, Column, String as _S, DateTime as _DT, ForeignKey as _FK, Integer as _I
from sqlalchemy.dialects.postgresql import UUID as _UUID
from sqlalchemy import insert as _insert
from app.core.deps import Base


metadata = MetaData()


class Asset:  # Placeholder for ORM class if needed by select queries
    __tablename__ = "assets"


def sa_insert_assets():
    t = Table(
        "assets",
        metadata,
        Column("id", _UUID(as_uuid=True)),
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


class Store(Base):
    __tablename__ = "stores"

    id = Column(_UUID(as_uuid=True), primary_key=True)
    name = Column(_S, nullable=False)
    address = Column(_S, nullable=True)


class StockLevel(Base):
    __tablename__ = "stock_levels"

    store_id = Column(_UUID(as_uuid=True), _FK("stores.id", ondelete="CASCADE"), primary_key=True)
    sku = Column(_S, primary_key=True)
    qty = Column(_I, nullable=False)


class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(_UUID(as_uuid=True), primary_key=True)
    store_id = Column(_UUID(as_uuid=True), _FK("stores.id", ondelete="CASCADE"), nullable=False)
    sku = Column(_S, nullable=False)
    delta_qty = Column(_I, nullable=False)
    incident_id = Column(_UUID(as_uuid=True), _FK("incidents.id", ondelete="SET NULL"), nullable=True)
    notes = Column(_S, nullable=True)
    created_at = Column(_DT(timezone=True), nullable=False)


