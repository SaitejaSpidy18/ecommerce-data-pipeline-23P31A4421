-- sql/ddl/create_staging_schema.sql
-- Staging schema: minimal constraints, raw data landing zone

DROP SCHEMA IF EXISTS staging CASCADE;
CREATE SCHEMA staging;

-- Staging Customers Table
CREATE TABLE staging.customers (
    customer_id INT,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(150),
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100),
    signup_date DATE,
    is_active BOOLEAN,
    load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Staging Products Table
CREATE TABLE staging.products (
    product_id INT,
    product_name VARCHAR(200),
    category VARCHAR(100),
    cost DECIMAL(10, 2),
    price DECIMAL(10, 2),
    stock_quantity INT,
    is_active BOOLEAN,
    created_date DATE,
    load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Staging Transactions Table
CREATE TABLE staging.transactions (
    transaction_id INT,
    customer_id INT,
    transaction_date DATE,
    payment_method VARCHAR(50),
    total_amount DECIMAL(12, 2),
    transaction_status VARCHAR(50),
    load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Staging Transaction Items Table
CREATE TABLE staging.transaction_items (
    item_id INT,
    transaction_id INT,
    product_id INT,
    quantity INT,
    unit_price DECIMAL(10, 2),
    line_total DECIMAL(12, 2),
    load_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create basic indexes for performance
CREATE INDEX idx_staging_customers_id ON staging.customers(customer_id);
CREATE INDEX idx_staging_products_id ON staging.products(product_id);
CREATE INDEX idx_staging_transactions_id ON staging.transactions(transaction_id);
CREATE INDEX idx_staging_transaction_items_id ON staging.transaction_items(item_id);

COMMIT;
