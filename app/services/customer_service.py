import math
import uuid

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.customer import CustomerCreate
from app.utils.exceptions import ConflictException, NotFoundException


class CustomerService:
    @staticmethod
    def create(db: Session, data: CustomerCreate) -> Customer:
        customer = Customer(**data.model_dump())
        db.add(customer)
        try:
            db.commit()
            db.refresh(customer)
            return customer
        except IntegrityError:
            db.rollback()
            raise ConflictException(f"Customer with email '{data.email}' already exists")

    @staticmethod
    def get_all(
        db: Session,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[Customer], int]:
        query = db.query(Customer)
        total = query.count()
        customers = (
            query.order_by(Customer.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return customers, total

    @staticmethod
    def get_by_id(db: Session, customer_id: uuid.UUID) -> Customer:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise NotFoundException("Customer not found")
        return customer

    @staticmethod
    def delete(db: Session, customer_id: uuid.UUID) -> None:
        customer = CustomerService.get_by_id(db, customer_id)
        db.delete(customer)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise ConflictException("Cannot delete customer with existing orders")

    @staticmethod
    def count(db: Session) -> int:
        return db.query(func.count(Customer.id)).scalar() or 0

    @staticmethod
    def paginate_meta(total: int, page: int, limit: int) -> dict:
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": math.ceil(total / limit) if total > 0 else 0,
        }
