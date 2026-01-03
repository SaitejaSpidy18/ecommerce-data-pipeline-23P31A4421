CREATE TABLE IF NOT EXISTS staging.products (
    product_id   INTEGER,
    product_name TEXT,
    category     TEXT,
    price        NUMERIC(10,2),
    is_active    BOOLEAN
);
