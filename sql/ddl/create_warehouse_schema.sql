-- sql/ddl/create_warehouse_schema.sql
-- Warehouse schema: Star schema with dimensions, facts, and aggregates

DROP SCHEMA IF EXISTS warehouse CASCADE;
CREATE SCHEMA warehouse;

-- ============================================
-- DIMENSION TABLES
-- ============================================

-- Dimension: Date
CREATE TABLE warehouse.dim_date (
    date_key INT PRIMARY KEY,
    date_value DATE NOT NULL UNIQUE,
    year INT,
    quarter INT,
    month INT,
    day INT,
    day_of_week INT,
    week_of_year INT,
    is_weekend BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Populate dim_date for 2024
INSERT INTO warehouse.dim_date 
SELECT 
    CAST(TO_CHAR(d, 'YYYYMMDD') AS INT) as date_key,
    d as date_value,
    EXTRACT(YEAR FROM d)::INT as year,
    EXTRACT(QUARTER FROM d)::INT as quarter,
    EXTRACT(MONTH FROM d)::INT as month,
    EXTRACT(DAY FROM d)::INT as day,
    EXTRACT(DOW FROM d)::INT as day_of_week,
    EXTRACT(WEEK FROM d)::INT as week_of_year,
    EXTRACT(DOW FROM d) IN (0, 6) as is_weekend,
    CURRENT_TIMESTAMP
FROM (
    SELECT DATE '2024-01-01' + (i || ' days')::INTERVAL as d
    FROM GENERATE_SERIES(0, 364) i
) dates
ON CONFLICT DO NOTHING;

-- Dimension: Customers (SCD Type 2)
CREATE TABLE warehouse.dim_customers (
    customer_key SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(150),
    phone VARCHAR(20),
    city VARCHAR(100),
    state VARCHAR(100),
    country VARCHAR(100),
    signup_date DATE,
    is_active BOOLEAN,
    effective_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_customers_id ON warehouse.dim_customers(customer_id);
CREATE INDEX idx_dim_customers_current ON warehouse.dim_customers(is_current);

-- Dimension: Products (SCD Type 2)
CREATE TABLE warehouse.dim_products (
    product_key SERIAL PRIMARY KEY,
    product_id INT NOT NULL,
    product_name VARCHAR(200),
    category VARCHAR(100),
    cost DECIMAL(10, 2),
    price DECIMAL(10, 2),
    is_active BOOLEAN,
    created_date DATE,
    effective_date DATE,
    end_date DATE,
    is_current BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_dim_products_id ON warehouse.dim_products(product_id);
CREATE INDEX idx_dim_products_current ON warehouse.dim_products(is_current);

-- Dimension: Payment Methods
CREATE TABLE warehouse.dim_payment_method (
    payment_method_key SERIAL PRIMARY KEY,
    payment_method_name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO warehouse.dim_payment_method (payment_method_name) VALUES
('Credit Card'),
('Debit Card'),
('UPI'),
('Net Banking'),
('Cash'),
('Unknown');

-- Dimension: Transaction Status
CREATE TABLE warehouse.dim_transaction_status (
    status_key SERIAL PRIMARY KEY,
    status_name VARCHAR(50) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO warehouse.dim_transaction_status (status_name) VALUES
('Completed'),
('Pending'),
('Failed'),
('Unknown');

-- ============================================
-- FACT TABLE
-- ============================================

-- Fact: Sales
CREATE TABLE warehouse.fact_sales (
    sales_key SERIAL PRIMARY KEY,
    transaction_id INT NOT NULL,
    customer_key INT NOT NULL,
    product_key INT NOT NULL,
    date_key INT NOT NULL,
    payment_method_key INT NOT NULL,
    status_key INT NOT NULL,
    quantity INT,
    unit_price DECIMAL(10, 2),
    line_total DECIMAL(12, 2),
    transaction_total DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_key) REFERENCES warehouse.dim_customers(customer_key),
    FOREIGN KEY (product_key) REFERENCES warehouse.dim_products(product_key),
    FOREIGN KEY (date_key) REFERENCES warehouse.dim_date(date_key),
    FOREIGN KEY (payment_method_key) REFERENCES warehouse.dim_payment_method(payment_method_key),
    FOREIGN KEY (status_key) REFERENCES warehouse.dim_transaction_status(status_key)
);

CREATE INDEX idx_fact_sales_customer ON warehouse.fact_sales(customer_key);
CREATE INDEX idx_fact_sales_product ON warehouse.fact_sales(product_key);
CREATE INDEX idx_fact_sales_date ON warehouse.fact_sales(date_key);
CREATE INDEX idx_fact_sales_transaction ON warehouse.fact_sales(transaction_id);

-- ============================================
-- AGGREGATE TABLES
-- ============================================

-- Aggregate: Daily Sales
CREATE TABLE warehouse.agg_daily_sales (
    agg_key SERIAL PRIMARY KEY,
    date_key INT NOT NULL,
    total_sales DECIMAL(14, 2),
    total_quantity INT,
    num_transactions INT,
    num_customers INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (date_key) REFERENCES warehouse.dim_date(date_key)
);

CREATE INDEX idx_agg_daily_date ON warehouse.agg_daily_sales(date_key);

-- Aggregate: Product Performance
CREATE TABLE warehouse.agg_product_performance (
    agg_key SERIAL PRIMARY KEY,
    product_key INT NOT NULL,
    total_sales DECIMAL(14, 2),
    total_quantity INT,
    num_transactions INT,
    avg_price DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_key) REFERENCES warehouse.dim_products(product_key)
);

CREATE INDEX idx_agg_product_key ON warehouse.agg_product_performance(product_key);

-- Aggregate: Customer Metrics
CREATE TABLE warehouse.agg_customer_metrics (
    agg_key SERIAL PRIMARY KEY,
    customer_key INT NOT NULL,
    total_spent DECIMAL(14, 2),
    total_purchases INT,
    num_transactions INT,
    avg_transaction_value DECIMAL(10, 2),
    last_purchase_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_key) REFERENCES warehouse.dim_customers(customer_key)
);

CREATE INDEX idx_agg_customer_key ON warehouse.agg_customer_metrics(customer_key);

COMMIT;
