CREATE TABLE IF NOT EXISTS warehouse.dim_product (
    product_sk      SERIAL PRIMARY KEY,
    product_id      INTEGER NOT NULL,
    product_name    TEXT NOT NULL,
    category        TEXT NOT NULL,
    price           NUMERIC(10,2) NOT NULL,
    is_active       BOOLEAN NOT NULL,
    is_current      BOOLEAN NOT NULL DEFAULT TRUE,
    valid_from      TIMESTAMP NOT NULL,
    valid_to        TIMESTAMP,
    CONSTRAINT uq_dim_product_business
        UNIQUE (product_id, valid_from)
);
CREATE INDEX IF NOT EXISTS idx_dim_product_id
    ON warehouse.dim_product(product_id);
