import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.order import OrderCreate, OrderListResponse, OrderResponse
from app.services.order_service import OrderService

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(data: OrderCreate, db: Session = Depends(get_db)):
    return OrderService.create(db, data)


@router.get("", response_model=OrderListResponse)
def list_orders(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    orders, total = OrderService.get_all(db, page=page, limit=limit)
    meta = OrderService.paginate_meta(total, page, limit)
    return OrderListResponse(items=orders, **meta)


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(order_id: uuid.UUID, db: Session = Depends(get_db)):
    return OrderService.get_by_id(db, order_id)


@router.delete("/{order_id}", response_model=OrderResponse)
def cancel_order(order_id: uuid.UUID, db: Session = Depends(get_db)):
    return OrderService.cancel(db, order_id)
