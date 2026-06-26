import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.customer import (
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
)
from app.services.customer_service import CustomerService

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(data: CustomerCreate, db: Session = Depends(get_db)):
    return CustomerService.create(db, data)


@router.get("", response_model=CustomerListResponse)
def list_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    customers, total = CustomerService.get_all(db, page=page, limit=limit)
    meta = CustomerService.paginate_meta(total, page, limit)
    return CustomerListResponse(items=customers, **meta)


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: uuid.UUID, db: Session = Depends(get_db)):
    return CustomerService.get_by_id(db, customer_id)


@router.delete("/{customer_id}", status_code=status.HTTP_200_OK)
def delete_customer(customer_id: uuid.UUID, db: Session = Depends(get_db)):
    CustomerService.delete(db, customer_id)
    return {"success": True, "message": "Customer deleted successfully"}
