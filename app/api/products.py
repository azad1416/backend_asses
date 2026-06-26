import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.product import (
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, db: Session = Depends(get_db)):
    return ProductService.create(db, data)


@router.get("", response_model=ProductListResponse)
def list_products(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    search: str | None = Query(None),
    db: Session = Depends(get_db),
):
    products, total = ProductService.get_all(db, page=page, limit=limit, search=search)
    meta = ProductService.paginate_meta(total, page, limit)
    return ProductListResponse(items=products, **meta)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    return ProductService.get_by_id(db, product_id)


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: uuid.UUID,
    data: ProductUpdate,
    db: Session = Depends(get_db),
):
    return ProductService.update(db, product_id, data)


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    ProductService.delete(db, product_id)
    return {"success": True, "message": "Product deleted successfully"}
