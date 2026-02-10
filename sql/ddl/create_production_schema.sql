-- sql/ddl/create_production_schema.sql
-- Production schema: 3NF, full constraints, cleaned & validated data

DROP SCHEMA IF EXISTS production CASCADE;
CREATE SCHEMA production;

-- Production Customers Table (3NF)
CREATE TABLE production.customers (
    customer_id INT PRIMARY KEY,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    phone VARCHAR(20),
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(100),
    postal_code VARCHAR(20),
    country VARCHAR(100) DEFAULT 'India',
    signup_date DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_email_format CHECK (email LIKE '%@%.%')
);

-- Production Products Table (3NF)
CREATE TABLE production.products (
    product_id INT PRIMARY KEY,
    product_name VARCHAR(200) NOT NULL,
    category VARCHAR(100) NOT NULL,
    cost DECIMAL(10, 2) NOT NULL CHECK (cost > 0),
    price DECIMAL(10, 2) NOT NULL CHECK (price > 0),
    stock_quantity INT DEFAULT 0 CHECK (stock_quantity >= 0),
    is_active BOOLEAN DEFAULT TRUE,
    created_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_price_gt_cost CHECK (price >= cost)
);

-- Production Transactions Table (3NF)
CREATE TABLE production.transactions (
    transaction_id INT PRIMARY KEY,
    customer_id INT NOT NULL,
    transaction_date DATE NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    total_amount DECIMAL(12, 2) NOT NULL CHECK (total_amount > 0),
    transaction_status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES production.customers(customer_id) ON DELETE RESTRICT
);

-- Production Transaction Items Table (3NF)
CREATE TABLE production.transaction_items (
    item_id INT PRIMARY KEY,
    transaction_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10, 2) NOT NULL CHECK (unit_price > 0),
    line_total DECIMAL(12, 2) NOT NULL CHECK (line_total > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transaction_id) REFERENCES production.transactions(transaction_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES production.products(product_id) ON DELETE RESTRICT,
    CONSTRAINT chk_line_total_calc CHECK (line_total = quantity * unit_price)
);

-- Create indexes for performance
CREATE INDEX idx_prod_customers_email ON production.customers(email);
CREATE INDEX idx_prod_customers_active ON production.customers(is_active);
CREATE INDEX idx_prod_products_category ON production.products(category);
CREATE INDEX idx_prod_products_active ON production.products(is_active);
CREATE INDEX idx_prod_transactions_customer ON production.transactions(customer_id);
CREATE INDEX idx_prod_transactions_date ON production.transactions(transaction_date);
CREATE INDEX idx_prod_transactions_status ON production.transactions(transaction_status);
CREATE INDEX idx_prod_items_transaction ON production.transaction_items(transaction_id);
CREATE INDEX idx_prod_items_product ON production.transaction_items(product_id);

COMMIT;
