CREATE TABLE IF NOT EXISTS production.products (
    product_id   INTEGER PRIMARY KEY,
    product_name TEXT NOT NULL,
    category     TEXT NOT NULL,
    price        NUMERIC(10,2) NOT NULL CHECK (price >= 0),
    is_active    BOOLEAN NOT NULL
);
