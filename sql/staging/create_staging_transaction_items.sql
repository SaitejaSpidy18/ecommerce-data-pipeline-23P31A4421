CREATE TABLE IF NOT EXISTS staging.transaction_items (
    transaction_item_id INTEGER,
    transaction_id      INTEGER,
    product_id          INTEGER,
    quantity            INTEGER
);
