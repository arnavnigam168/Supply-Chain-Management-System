-- Inventory & Supply Chain Management System
-- Database: inventory_supply_chain
-- Run this script to create database, tables, indexes, and trigger

CREATE DATABASE IF NOT EXISTS inventory_supply_chain;
USE inventory_supply_chain;

-- 1. Suppliers
CREATE TABLE Suppliers (
    supplier_id INT PRIMARY KEY AUTO_INCREMENT,
    supplier_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255),
    phone VARCHAR(15) NOT NULL,
    email VARCHAR(255),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(100),
    CONSTRAINT uq_suppliers_phone UNIQUE (phone)
);

-- 2. Categories
CREATE TABLE Categories (
    category_id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(255) NOT NULL,
    description VARCHAR(255)
);

-- 3. Products
CREATE TABLE Products (
    product_id INT PRIMARY KEY AUTO_INCREMENT,
    product_name VARCHAR(255) NOT NULL,
    category_id INT,
    supplier_id INT,
    unit_price DECIMAL(10,2),
    unit_type VARCHAR(50),
    description VARCHAR(255),
    CONSTRAINT ck_products_unit_price_positive CHECK (unit_price > 0),
    CONSTRAINT fk_products_category FOREIGN KEY (category_id)
        REFERENCES Categories(category_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_products_supplier FOREIGN KEY (supplier_id)
        REFERENCES Suppliers(supplier_id) ON DELETE SET NULL ON UPDATE CASCADE
);
CREATE INDEX ix_products_category_id ON Products(category_id);
CREATE INDEX ix_products_supplier_id ON Products(supplier_id);

-- 4. Inventory
CREATE TABLE Inventory (
    inventory_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL UNIQUE,
    quantity_available INT NOT NULL DEFAULT 0,
    reorder_level INT NOT NULL DEFAULT 0,
    last_updated DATE NOT NULL DEFAULT (CURRENT_DATE),
    CONSTRAINT fk_inventory_product FOREIGN KEY (product_id)
        REFERENCES Products(product_id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX ix_inventory_product_id ON Inventory(product_id);

-- 5. Purchase_Orders
CREATE TABLE Purchase_Orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    supplier_id INT,
    order_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    expected_delivery_date DATE,
    status VARCHAR(50) NOT NULL DEFAULT 'Pending',
    CONSTRAINT fk_purchase_orders_supplier FOREIGN KEY (supplier_id)
        REFERENCES Suppliers(supplier_id) ON DELETE SET NULL ON UPDATE CASCADE
);
CREATE INDEX ix_purchase_orders_supplier_id ON Purchase_Orders(supplier_id);

-- 6. Purchase_Order_Details
CREATE TABLE Purchase_Order_Details (
    order_detail_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    product_id INT,
    quantity_ordered INT NOT NULL DEFAULT 1,
    total_price DECIMAL(10,2) NOT NULL DEFAULT 0,
    CONSTRAINT fk_purchase_order_details_order FOREIGN KEY (order_id)
        REFERENCES Purchase_Orders(order_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_purchase_order_details_product FOREIGN KEY (product_id)
        REFERENCES Products(product_id) ON DELETE SET NULL ON UPDATE CASCADE
);
CREATE INDEX ix_purchase_order_details_order_id ON Purchase_Order_Details(order_id);
CREATE INDEX ix_purchase_order_details_product_id ON Purchase_Order_Details(product_id);

-- 7. Stock_Transactions
CREATE TABLE Stock_Transactions (
    transaction_id INT PRIMARY KEY AUTO_INCREMENT,
    product_id INT NOT NULL,
    transaction_type VARCHAR(20) NOT NULL,
    quantity INT NOT NULL,
    transaction_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    CONSTRAINT ck_stock_transactions_quantity_positive CHECK (quantity > 0),
    CONSTRAINT ck_stock_transactions_type_allowed CHECK (transaction_type IN ('IN', 'OUT', 'ADJUSTMENT')),
    CONSTRAINT fk_stock_transactions_product FOREIGN KEY (product_id)
        REFERENCES Products(product_id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX ix_stock_transactions_product_id ON Stock_Transactions(product_id);

DELIMITER //
CREATE TRIGGER trg_update_inventory_after_stock_insert
AFTER INSERT ON Stock_Transactions
FOR EACH ROW
BEGIN
    INSERT INTO Inventory (product_id, quantity_available, reorder_level, last_updated)
    VALUES (
        NEW.product_id,
        CASE
            WHEN NEW.transaction_type = 'IN' THEN NEW.quantity
            WHEN NEW.transaction_type = 'OUT' THEN -NEW.quantity
            ELSE NEW.quantity
        END,
        0,
        NEW.transaction_date
    )
    ON DUPLICATE KEY UPDATE
        quantity_available = CASE
            WHEN NEW.transaction_type = 'IN' THEN quantity_available + NEW.quantity
            WHEN NEW.transaction_type = 'OUT' THEN quantity_available - NEW.quantity
            ELSE NEW.quantity
        END,
        last_updated = NEW.transaction_date;
END//
DELIMITER ;
