import math
import uuid

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate
from app.utils.exceptions import ConflictException, NotFoundException


class ProductService:
    @staticmethod
    def create(db: Session, data: ProductCreate) -> Product:
        product = Product(**data.model_dump())
        db.add(product)
        try:
            db.commit()
            db.refresh(product)
            return product
        except IntegrityError:
            db.rollback()
            raise ConflictException(f"Product with SKU '{data.sku}' already exists")

    @staticmethod
    def get_all(
        db: Session,
        page: int = 1,
        limit: int = 10,
        search: str | None = None,
    ) -> tuple[list[Product], int]:
        query = db.query(Product)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    Product.sku.ilike(search_term),
                )
            )

        total = query.count()
        products = (
            query.order_by(Product.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return products, total

    @staticmethod
    def get_by_id(db: Session, product_id: uuid.UUID) -> Product:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise NotFoundException("Product not found")
        return product

    @staticmethod
    def update(db: Session, product_id: uuid.UUID, data: ProductUpdate) -> Product:
        product = ProductService.get_by_id(db, product_id)
        update_data = data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            setattr(product, field, value)

        try:
            db.commit()
            db.refresh(product)
            return product
        except IntegrityError:
            db.rollback()
            raise ConflictException("Product with this SKU already exists")

    @staticmethod
    def delete(db: Session, product_id: uuid.UUID) -> None:
        product = ProductService.get_by_id(db, product_id)
        db.delete(product)
        db.commit()

    @staticmethod
    def count(db: Session) -> int:
        return db.query(func.count(Product.id)).scalar() or 0

    @staticmethod
    def count_low_stock(db: Session, threshold: int) -> int:
        return (
            db.query(func.count(Product.id))
            .filter(Product.stock_quantity < threshold)
            .scalar()
            or 0
        )

    @staticmethod
    def paginate_meta(total: int, page: int, limit: int) -> dict:
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": math.ceil(total / limit) if total > 0 else 0,
        }
