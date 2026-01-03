CREATE TABLE IF NOT EXISTS warehouse.fact_sales (
    sales_sk            BIGSERIAL PRIMARY KEY,
    transaction_id      INTEGER NOT NULL,
    transaction_item_id INTEGER NOT NULL,
    date_key            INTEGER NOT NULL,
    customer_sk         INTEGER NOT NULL,
    product_sk          INTEGER NOT NULL,
    quantity            INTEGER NOT NULL,
    unit_price          NUMERIC(10,2) NOT NULL,
    total_amount        NUMERIC(12,2) NOT NULL,
    payment_method      TEXT NOT NULL,
    currency            TEXT NOT NULL,
    CONSTRAINT fk_fact_sales_dim_date
        FOREIGN KEY (date_key)
        REFERENCES warehouse.dim_date(date_key),
    CONSTRAINT fk_fact_sales_dim_customer
        FOREIGN KEY (customer_sk)
        REFERENCES warehouse.dim_customer(customer_sk),
    CONSTRAINT fk_fact_sales_dim_product
        FOREIGN KEY (product_sk)
        REFERENCES warehouse.dim_product(product_sk)
);
CREATE INDEX IF NOT EXISTS idx_fact_sales_date_key
    ON warehouse.fact_sales(date_key);
CREATE INDEX IF NOT EXISTS idx_fact_sales_customer
    ON warehouse.fact_sales(customer_sk);
CREATE INDEX IF NOT EXISTS idx_fact_sales_product
    ON warehouse.fact_sales(product_sk);
