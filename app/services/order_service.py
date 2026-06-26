import math
import uuid
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.product import Product
from app.schemas.order import OrderCreate
from app.services.customer_service import CustomerService
from app.services.product_service import ProductService
from app.utils.exceptions import BadRequestException, NotFoundException


class OrderService:
    @staticmethod
    def create(db: Session, data: OrderCreate) -> Order:
        CustomerService.get_by_id(db, data.customer_id)

        product_ids = [item.product_id for item in data.items]
        if len(product_ids) != len(set(product_ids)):
            raise BadRequestException("Duplicate products in order are not allowed")

        products: dict[uuid.UUID, Product] = {}
        for product_id in product_ids:
            product = db.query(Product).filter(Product.id == product_id).with_for_update().first()
            if not product:
                raise NotFoundException(f"Product with id '{product_id}' not found")
            products[product_id] = product

        order_items_data: list[dict] = []
        total_amount = Decimal("0.00")

        for item in data.items:
            product = products[item.product_id]
            if product.stock_quantity < item.quantity:
                raise BadRequestException(
                    f"Insufficient inventory for product '{product.name}'. "
                    f"Available: {product.stock_quantity}, Requested: {item.quantity}"
                )

            unit_price = product.price
            subtotal = (unit_price * item.quantity).quantize(Decimal("0.01"))
            total_amount += subtotal

            order_items_data.append(
                {
                    "product_id": product.id,
                    "quantity": item.quantity,
                    "unit_price": unit_price,
                    "subtotal": subtotal,
                }
            )

        try:
            order = Order(
                customer_id=data.customer_id,
                total_amount=total_amount,
                status=OrderStatus.PENDING,
            )
            db.add(order)
            db.flush()

            for item_data in order_items_data:
                order_item = OrderItem(order_id=order.id, **item_data)
                db.add(order_item)
                product = products[item_data["product_id"]]
                product.stock_quantity -= item_data["quantity"]

            db.commit()
            return OrderService.get_by_id(db, order.id)
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def get_all(
        db: Session,
        page: int = 1,
        limit: int = 10,
    ) -> tuple[list[Order], int]:
        query = db.query(Order)
        total = query.count()
        orders = (
            query.options(
                joinedload(Order.customer),
                joinedload(Order.items).joinedload(OrderItem.product),
            )
            .order_by(Order.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
            .all()
        )
        return orders, total

    @staticmethod
    def get_by_id(db: Session, order_id: uuid.UUID) -> Order:
        order = (
            db.query(Order)
            .options(
                joinedload(Order.customer),
                joinedload(Order.items).joinedload(OrderItem.product),
            )
            .filter(Order.id == order_id)
            .first()
        )
        if not order:
            raise NotFoundException("Order not found")
        return order

    @staticmethod
    def cancel(db: Session, order_id: uuid.UUID) -> Order:
        order = (
            db.query(Order)
            .options(joinedload(Order.items))
            .filter(Order.id == order_id)
            .with_for_update()
            .first()
        )
        if not order:
            raise NotFoundException("Order not found")

        if order.status == OrderStatus.CANCELLED:
            raise BadRequestException("Order is already cancelled")

        if order.status == OrderStatus.COMPLETED:
            raise BadRequestException("Cannot cancel a completed order")

        try:
            for item in order.items:
                product = (
                    db.query(Product)
                    .filter(Product.id == item.product_id)
                    .with_for_update()
                    .first()
                )
                if product:
                    product.stock_quantity += item.quantity

            order.status = OrderStatus.CANCELLED
            db.commit()
            return OrderService.get_by_id(db, order.id)
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def count(db: Session) -> int:
        return db.query(func.count(Order.id)).scalar() or 0

    @staticmethod
    def paginate_meta(total: int, page: int, limit: int) -> dict:
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "pages": math.ceil(total / limit) if total > 0 else 0,
        }
