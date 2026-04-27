from sqlalchemy import CheckConstraint, Index, text
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Supplier(db.Model):
    __tablename__ = "Suppliers"

    supplier_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    supplier_name = db.Column(db.String(255), nullable=False)
    contact_person = db.Column(db.String(255))
    phone = db.Column(db.String(15), nullable=False, unique=True)
    email = db.Column(db.String(255))
    address = db.Column(db.String(255))
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))


class Category(db.Model):
    __tablename__ = "Categories"

    category_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(255))


class Product(db.Model):
    __tablename__ = "Products"

    product_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String(255), nullable=False)
    category_id = db.Column(
        db.Integer,
        db.ForeignKey("Categories.category_id", ondelete="SET NULL"),
        index=True,
    )
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("Suppliers.supplier_id", ondelete="SET NULL"),
        index=True,
    )
    unit_price = db.Column(db.Numeric(10, 2))
    unit_type = db.Column(db.String(50))
    description = db.Column(db.String(255))

    __table_args__ = (
        CheckConstraint("unit_price > 0", name="ck_products_unit_price_positive"),
    )


class Inventory(db.Model):
    __tablename__ = "Inventory"

    inventory_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("Products.product_id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    quantity_available = db.Column(db.Integer, nullable=False, server_default=text("0"))
    reorder_level = db.Column(db.Integer, nullable=False, server_default=text("0"))
    last_updated = db.Column(db.Date, nullable=False, server_default=text("(CURRENT_DATE)"))


class PurchaseOrder(db.Model):
    __tablename__ = "Purchase_Orders"

    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    supplier_id = db.Column(
        db.Integer,
        db.ForeignKey("Suppliers.supplier_id", ondelete="SET NULL"),
        index=True,
    )
    order_date = db.Column(db.Date, nullable=False, server_default=text("(CURRENT_DATE)"))
    expected_delivery_date = db.Column(db.Date)
    status = db.Column(
        db.String(50),
        nullable=False,
        server_default=text("'Pending'"),
    )


class PurchaseOrderDetail(db.Model):
    __tablename__ = "Purchase_Order_Details"

    order_detail_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(
        db.Integer,
        db.ForeignKey("Purchase_Orders.order_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("Products.product_id", ondelete="SET NULL"),
        index=True,
    )
    quantity_ordered = db.Column(db.Integer, nullable=False, server_default=text("1"))
    total_price = db.Column(db.Numeric(10, 2), nullable=False, server_default=text("0"))


class StockTransaction(db.Model):
    __tablename__ = "Stock_Transactions"

    transaction_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_id = db.Column(
        db.Integer,
        db.ForeignKey("Products.product_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    transaction_type = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    transaction_date = db.Column(db.Date, nullable=False, server_default=text("(CURRENT_DATE)"))

    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_stock_transactions_quantity_positive"),
        CheckConstraint(
            "transaction_type IN ('IN','OUT','ADJUSTMENT')",
            name="ck_stock_transactions_type_allowed",
        ),
    )


Index("ix_purchase_orders_supplier_id", PurchaseOrder.supplier_id)
