from datetime import date, datetime
from decimal import Decimal, InvalidOperation
import os

from flask import Flask, flash, redirect, render_template, request, url_for
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from models import (
    Category,
    Inventory,
    Product,
    PurchaseOrder,
    PurchaseOrderDetail,
    StockTransaction,
    Supplier,
    db,
)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:Mhryas%4009934@localhost:3306/inventory_supply_chain"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)


def to_int(value, field_name, minimum=None, allow_empty=False):
    if allow_empty and (value is None or value == ""):
        return None
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid integer.")
    if minimum is not None and parsed < minimum:
        raise ValueError(f"{field_name} must be at least {minimum}.")
    return parsed


def to_decimal(value, field_name, minimum=None, allow_empty=False):
    if allow_empty and (value is None or value == ""):
        return None
    try:
        parsed = Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid number.")
    if minimum is not None and parsed <= Decimal(str(minimum)):
        raise ValueError(f"{field_name} must be greater than {minimum}.")
    return parsed


def to_date(value, field_name, allow_empty=True):
    if allow_empty and (value is None or value == ""):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        raise ValueError(f"{field_name} must be a valid date (YYYY-MM-DD).")


def commit_with_message(success_message, redirect_endpoint, **redirect_values):
    try:
        db.session.commit()
        flash(success_message, "success")
    except IntegrityError as error:
        db.session.rollback()
        flash(f"Database constraint error: {error.orig}", "danger")
    except SQLAlchemyError as error:
        db.session.rollback()
        flash(f"Database error: {error}", "danger")
    return redirect(url_for(redirect_endpoint, **redirect_values))


@app.route("/")
def index():
    total_products = db.session.query(Product).count()
    total_suppliers = db.session.query(Supplier).count()
    total_stock = db.session.query(db.func.coalesce(db.func.sum(Inventory.quantity_available), 0)).scalar()
    recent_transactions = (
        db.session.query(StockTransaction, Product.product_name)
        .join(Product, StockTransaction.product_id == Product.product_id)
        .order_by(StockTransaction.transaction_date.desc(), StockTransaction.transaction_id.desc())
        .limit(8)
        .all()
    )
    return render_template(
        "index.html",
        total_products=total_products,
        total_suppliers=total_suppliers,
        total_stock=total_stock,
        recent_transactions=recent_transactions,
    )


@app.route("/suppliers")
def view_suppliers():
    suppliers = Supplier.query.order_by(Supplier.supplier_name.asc()).all()
    return render_template("suppliers_list.html", suppliers=suppliers)


@app.route("/suppliers/add", methods=["GET", "POST"])
def add_supplier():
    if request.method == "POST":
        try:
            supplier_name = request.form.get("supplier_name", "").strip()
            phone = request.form.get("phone", "").strip()
            if not supplier_name:
                raise ValueError("Supplier name is required.")
            if not phone:
                raise ValueError("Phone is required.")
            supplier = Supplier(
                supplier_name=supplier_name,
                contact_person=request.form.get("contact_person", "").strip() or None,
                phone=phone,
                email=request.form.get("email", "").strip() or None,
                address=request.form.get("address", "").strip() or None,
                city=request.form.get("city", "").strip() or None,
                state=request.form.get("state", "").strip() or None,
            )
            db.session.add(supplier)
            return commit_with_message("Supplier added successfully.", "view_suppliers")
        except ValueError as error:
            flash(str(error), "danger")
    return render_template("supplier_add.html", supplier=None)


@app.route("/suppliers/<int:supplier_id>/edit", methods=["GET", "POST"])
def edit_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    if request.method == "POST":
        try:
            supplier_name = request.form.get("supplier_name", "").strip()
            phone = request.form.get("phone", "").strip()
            if not supplier_name or not phone:
                raise ValueError("Supplier name and phone are required.")
            supplier.supplier_name = supplier_name
            supplier.contact_person = request.form.get("contact_person", "").strip() or None
            supplier.phone = phone
            supplier.email = request.form.get("email", "").strip() or None
            supplier.address = request.form.get("address", "").strip() or None
            supplier.city = request.form.get("city", "").strip() or None
            supplier.state = request.form.get("state", "").strip() or None
            return commit_with_message("Supplier updated successfully.", "view_suppliers")
        except ValueError as error:
            flash(str(error), "danger")
    return render_template("supplier_add.html", supplier=supplier)


@app.route("/suppliers/<int:supplier_id>/delete", methods=["POST"])
def delete_supplier(supplier_id):
    supplier = Supplier.query.get_or_404(supplier_id)
    db.session.delete(supplier)
    return commit_with_message("Supplier deleted successfully.", "view_suppliers")


@app.route("/categories")
def view_categories():
    categories = Category.query.order_by(Category.category_name.asc()).all()
    return render_template("categories_list.html", categories=categories)


@app.route("/categories/add", methods=["GET", "POST"])
def add_category():
    if request.method == "POST":
        category_name = request.form.get("category_name", "").strip()
        if not category_name:
            flash("Category name is required.", "danger")
        else:
            category = Category(
                category_name=category_name,
                description=request.form.get("description", "").strip() or None,
            )
            db.session.add(category)
            return commit_with_message("Category added successfully.", "view_categories")
    return render_template("category_add.html", category=None)


@app.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)
    if request.method == "POST":
        category_name = request.form.get("category_name", "").strip()
        if not category_name:
            flash("Category name is required.", "danger")
        else:
            category.category_name = category_name
            category.description = request.form.get("description", "").strip() or None
            return commit_with_message("Category updated successfully.", "view_categories")
    return render_template("category_add.html", category=category)


@app.route("/categories/<int:category_id>/delete", methods=["POST"])
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    return commit_with_message("Category deleted successfully.", "view_categories")


@app.route("/products")
def view_products():
    products = (
        db.session.query(Product, Category.category_name, Supplier.supplier_name)
        .outerjoin(Category, Product.category_id == Category.category_id)
        .outerjoin(Supplier, Product.supplier_id == Supplier.supplier_id)
        .order_by(Product.product_name.asc())
        .all()
    )
    return render_template("products_list.html", products=products)


@app.route("/products/add", methods=["GET", "POST"])
def add_product():
    categories = Category.query.order_by(Category.category_name.asc()).all()
    suppliers = Supplier.query.order_by(Supplier.supplier_name.asc()).all()
    if request.method == "POST":
        try:
            product_name = request.form.get("product_name", "").strip()
            if not product_name:
                raise ValueError("Product name is required.")
            product = Product(
                product_name=product_name,
                category_id=to_int(request.form.get("category_id"), "Category", allow_empty=True),
                supplier_id=to_int(request.form.get("supplier_id"), "Supplier", allow_empty=True),
                unit_price=to_decimal(request.form.get("unit_price"), "Unit price", minimum=0, allow_empty=True),
                unit_type=request.form.get("unit_type", "").strip() or None,
                description=request.form.get("description", "").strip() or None,
            )
            db.session.add(product)
            return commit_with_message("Product added successfully.", "view_products")
        except ValueError as error:
            flash(str(error), "danger")
    return render_template("product_add.html", categories=categories, suppliers=suppliers, product=None)


@app.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    categories = Category.query.order_by(Category.category_name.asc()).all()
    suppliers = Supplier.query.order_by(Supplier.supplier_name.asc()).all()
    if request.method == "POST":
        try:
            product_name = request.form.get("product_name", "").strip()
            if not product_name:
                raise ValueError("Product name is required.")
            product.product_name = product_name
            product.category_id = to_int(request.form.get("category_id"), "Category", allow_empty=True)
            product.supplier_id = to_int(request.form.get("supplier_id"), "Supplier", allow_empty=True)
            product.unit_price = to_decimal(request.form.get("unit_price"), "Unit price", minimum=0, allow_empty=True)
            product.unit_type = request.form.get("unit_type", "").strip() or None
            product.description = request.form.get("description", "").strip() or None
            return commit_with_message("Product updated successfully.", "view_products")
        except ValueError as error:
            flash(str(error), "danger")
    return render_template("product_add.html", categories=categories, suppliers=suppliers, product=product)


@app.route("/products/<int:product_id>/delete", methods=["POST"])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    return commit_with_message("Product deleted successfully.", "view_products")


@app.route("/inventory")
def view_inventory():
    inventory = (
        db.session.query(Inventory, Product.product_name)
        .join(Product, Inventory.product_id == Product.product_id)
        .order_by(Product.product_name.asc())
        .all()
    )
    return render_template("inventory_list.html", inventory=inventory)


@app.route("/inventory/add", methods=["GET", "POST"])
def add_inventory():
    products = Product.query.order_by(Product.product_name.asc()).all()
    if request.method == "POST":
        try:
            inventory = Inventory(
                product_id=to_int(request.form.get("product_id"), "Product"),
                quantity_available=to_int(request.form.get("quantity_available"), "Quantity", minimum=0),
                reorder_level=to_int(request.form.get("reorder_level"), "Reorder level", minimum=0),
                last_updated=to_date(request.form.get("last_updated"), "Last updated") or date.today(),
            )
            db.session.add(inventory)
            return commit_with_message("Inventory record added successfully.", "view_inventory")
        except ValueError as error:
            flash(str(error), "danger")
    return render_template("inventory_add.html", products=products, record=None)


@app.route("/inventory/<int:inventory_id>/edit", methods=["GET", "POST"])
def edit_inventory(inventory_id):
    record = Inventory.query.get_or_404(inventory_id)
    products = Product.query.order_by(Product.product_name.asc()).all()
    if request.method == "POST":
        try:
            record.product_id = to_int(request.form.get("product_id"), "Product")
            record.quantity_available = to_int(request.form.get("quantity_available"), "Quantity", minimum=0)
            record.reorder_level = to_int(request.form.get("reorder_level"), "Reorder level", minimum=0)
            record.last_updated = to_date(request.form.get("last_updated"), "Last updated") or date.today()
            return commit_with_message("Inventory record updated successfully.", "view_inventory")
        except ValueError as error:
            flash(str(error), "danger")
    return render_template("inventory_add.html", products=products, record=record)


@app.route("/inventory/<int:inventory_id>/delete", methods=["POST"])
def delete_inventory(inventory_id):
    record = Inventory.query.get_or_404(inventory_id)
    db.session.delete(record)
    return commit_with_message("Inventory record deleted successfully.", "view_inventory")


@app.route("/purchase-orders")
def view_purchase_orders():
    orders = (
        db.session.query(PurchaseOrder, Supplier.supplier_name)
        .outerjoin(Supplier, PurchaseOrder.supplier_id == Supplier.supplier_id)
        .order_by(PurchaseOrder.order_id.desc())
        .all()
    )
    return render_template("purchase_orders_list.html", orders=orders)


@app.route("/purchase-orders/add", methods=["GET", "POST"])
def add_purchase_order():
    suppliers = Supplier.query.order_by(Supplier.supplier_name.asc()).all()
    if request.method == "POST":
        try:
            purchase_order = PurchaseOrder(
                supplier_id=to_int(request.form.get("supplier_id"), "Supplier", allow_empty=True),
                order_date=to_date(request.form.get("order_date"), "Order date") or date.today(),
                expected_delivery_date=to_date(
                    request.form.get("expected_delivery_date"),
                    "Expected delivery date",
                ),
                status=(request.form.get("status") or "Pending").strip() or "Pending",
            )
            db.session.add(purchase_order)
            return commit_with_message("Purchase order created successfully.", "view_purchase_orders")
        except ValueError as error:
            flash(str(error), "danger")
    return render_template("purchase_order_add.html", suppliers=suppliers, order=None)


@app.route("/purchase-orders/<int:order_id>/edit", methods=["GET", "POST"])
def edit_purchase_order(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    suppliers = Supplier.query.order_by(Supplier.supplier_name.asc()).all()
    if request.method == "POST":
        try:
            order.supplier_id = to_int(request.form.get("supplier_id"), "Supplier", allow_empty=True)
            order.order_date = to_date(request.form.get("order_date"), "Order date") or date.today()
            order.expected_delivery_date = to_date(
                request.form.get("expected_delivery_date"),
                "Expected delivery date",
            )
            order.status = (request.form.get("status") or "Pending").strip() or "Pending"
            return commit_with_message("Purchase order updated successfully.", "view_purchase_orders")
        except ValueError as error:
            flash(str(error), "danger")
    return render_template("purchase_order_add.html", suppliers=suppliers, order=order)


@app.route("/purchase-orders/<int:order_id>/delete", methods=["POST"])
def delete_purchase_order(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    db.session.delete(order)
    return commit_with_message("Purchase order deleted successfully.", "view_purchase_orders")


@app.route("/purchase-order-details/add", methods=["GET", "POST"])
def add_purchase_order_detail():
    orders = PurchaseOrder.query.order_by(PurchaseOrder.order_id.desc()).all()
    products = Product.query.order_by(Product.product_name.asc()).all()
    if request.method == "POST":
        try:
            detail = PurchaseOrderDetail(
                order_id=to_int(request.form.get("order_id"), "Order"),
                product_id=to_int(request.form.get("product_id"), "Product", allow_empty=True),
                quantity_ordered=to_int(request.form.get("quantity_ordered"), "Quantity", minimum=1),
                total_price=to_decimal(request.form.get("total_price"), "Total price", minimum=0),
            )
            db.session.add(detail)
            return commit_with_message("Order detail added successfully.", "view_purchase_orders")
        except ValueError as error:
            flash(str(error), "danger")
    return render_template("purchase_order_detail_add.html", orders=orders, products=products)


@app.route("/stock-transactions")
def view_stock_transactions():
    transactions = (
        db.session.query(StockTransaction, Product.product_name)
        .join(Product, StockTransaction.product_id == Product.product_id)
        .order_by(StockTransaction.transaction_date.desc(), StockTransaction.transaction_id.desc())
        .all()
    )
    return render_template("stock_transactions_list.html", transactions=transactions)


@app.route("/stock-transactions/add", methods=["GET", "POST"])
def add_stock_transaction():
    products = Product.query.order_by(Product.product_name.asc()).all()
    if request.method == "POST":
        try:
            transaction_type = (request.form.get("transaction_type") or "").upper().strip()
            if transaction_type not in {"IN", "OUT", "ADJUSTMENT"}:
                raise ValueError("Transaction type must be IN, OUT, or ADJUSTMENT.")
            transaction = StockTransaction(
                product_id=to_int(request.form.get("product_id"), "Product"),
                transaction_type=transaction_type,
                quantity=to_int(request.form.get("quantity"), "Quantity", minimum=1),
                transaction_date=to_date(request.form.get("transaction_date"), "Transaction date")
                or date.today(),
            )
            db.session.add(transaction)
            return commit_with_message("Stock transaction added successfully.", "view_stock_transactions")
        except ValueError as error:
            flash(str(error), "danger")
    return render_template("stock_transaction_add.html", products=products, transaction=None)


@app.route("/stock-transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
def edit_stock_transaction(transaction_id):
    transaction = StockTransaction.query.get_or_404(transaction_id)
    products = Product.query.order_by(Product.product_name.asc()).all()
    if request.method == "POST":
        try:
            transaction_type = (request.form.get("transaction_type") or "").upper().strip()
            if transaction_type not in {"IN", "OUT", "ADJUSTMENT"}:
                raise ValueError("Transaction type must be IN, OUT, or ADJUSTMENT.")
            transaction.product_id = to_int(request.form.get("product_id"), "Product")
            transaction.transaction_type = transaction_type
            transaction.quantity = to_int(request.form.get("quantity"), "Quantity", minimum=1)
            transaction.transaction_date = (
                to_date(request.form.get("transaction_date"), "Transaction date") or date.today()
            )
            return commit_with_message("Stock transaction updated successfully.", "view_stock_transactions")
        except ValueError as error:
            flash(str(error), "danger")
    return render_template("stock_transaction_add.html", products=products, transaction=transaction)


@app.route("/stock-transactions/<int:transaction_id>/delete", methods=["POST"])
def delete_stock_transaction(transaction_id):
    transaction = StockTransaction.query.get_or_404(transaction_id)
    db.session.delete(transaction)
    return commit_with_message("Stock transaction deleted successfully.", "view_stock_transactions")


if __name__ == "__main__":
    app.run(debug=True)
