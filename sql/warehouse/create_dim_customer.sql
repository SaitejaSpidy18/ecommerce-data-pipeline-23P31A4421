CREATE TABLE IF NOT EXISTS warehouse.dim_customer (
    customer_sk     SERIAL PRIMARY KEY,
    customer_id     INTEGER NOT NULL,
    first_name      TEXT NOT NULL,
    last_name       TEXT NOT NULL,
    email           TEXT NOT NULL,
    country         TEXT NOT NULL,
    signup_date     DATE NOT NULL,
    is_current      BOOLEAN NOT NULL DEFAULT TRUE,
    valid_from      TIMESTAMP NOT NULL,
    valid_to        TIMESTAMP,
    CONSTRAINT uq_dim_customer_business
        UNIQUE (customer_id, valid_from)
);
CREATE INDEX IF NOT EXISTS idx_dim_customer_id
    ON warehouse.dim_customer(customer_id);
