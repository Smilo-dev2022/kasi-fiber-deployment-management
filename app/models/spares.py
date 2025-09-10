from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.deps import Base


class Store(Base):
    __tablename__ = "stores"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)


class StockLevel(Base):
    __tablename__ = "stock_levels"

    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="CASCADE"), primary_key=True)
    sku = Column(String, primary_key=True)
    qty = Column(Integer, nullable=False)


class SpareIssue(Base):
    __tablename__ = "spare_issues"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="SET NULL"))
    sku = Column(String, nullable=False)
    qty = Column(Integer, nullable=False)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"))
    to_user = Column(UUID(as_uuid=True), nullable=True)


class SpareReturn(Base):
    __tablename__ = "spare_returns"

    id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), nullable=True)
    store_id = Column(UUID(as_uuid=True), ForeignKey("stores.id", ondelete="SET NULL"))
    sku = Column(String, nullable=False)
    qty = Column(Integer, nullable=False)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"))
    by_user = Column(UUID(as_uuid=True), nullable=True)

