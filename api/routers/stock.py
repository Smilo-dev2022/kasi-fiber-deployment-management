from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..db.session import get_db
from ..models.stock import StockItem, StockIssue
from ..schemas.stock import StockItemOut, StockItemCreate, StockIssueOut, StockIssueCreate
from ..deps import get_current_user
from ..services.audit import audit


router = APIRouter(prefix="/stock", tags=["Stock"])


@router.get("/", response_model=List[StockItemOut])
def list_stock(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(StockItem).order_by(StockItem.sku).all()


@router.post("/items", response_model=StockItemOut)
def create_item(payload: StockItemCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    item = StockItem(sku=payload.sku, name=payload.name, unit=payload.unit, on_hand=payload.on_hand)
    db.add(item)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, detail="SKU already exists")
    db.refresh(item)
    audit(db, "StockItem", item.id, "CREATE", user.id, None, {"sku": item.sku})
    db.commit()
    return item


@router.post("/issues", response_model=StockIssueOut)
def issue_stock(payload: StockIssueCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    item = db.get(StockItem, payload.item_id)
    if not item:
        raise HTTPException(404, detail="Item not found")
    if item.on_hand - payload.quantity < 0:
        raise HTTPException(400, detail="Insufficient stock")
    item.on_hand -= payload.quantity
    issue = StockIssue(item_id=item.id, pon_id=payload.pon_id, issued_to=user.id, quantity=payload.quantity)
    db.add(issue)
    db.add(item)
    db.commit()
    db.refresh(issue)
    audit(db, "StockIssue", issue.id, "CREATE", user.id, None, {"item_id": issue.item_id, "qty": issue.quantity})
    db.commit()
    return issue

