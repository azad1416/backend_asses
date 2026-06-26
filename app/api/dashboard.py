from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.order import DashboardResponse
from app.services.customer_service import CustomerService
from app.services.order_service import OrderService
from app.services.product_service import ProductService

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
settings = get_settings()


@router.get("", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)):
    return DashboardResponse(
        total_products=ProductService.count(db),
        total_customers=CustomerService.count(db),
        total_orders=OrderService.count(db),
        low_stock_products=ProductService.count_low_stock(
            db, settings.low_stock_threshold
        ),
    )
