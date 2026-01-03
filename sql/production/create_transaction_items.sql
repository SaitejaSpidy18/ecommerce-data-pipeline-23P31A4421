CREATE TABLE IF NOT EXISTS production.transaction_items (
    transaction_item_id INTEGER PRIMARY KEY,
    transaction_id      INTEGER NOT NULL,
    product_id          INTEGER NOT NULL,
    quantity            INTEGER NOT NULL CHECK (quantity > 0),
    CONSTRAINT fk_tx_items_transaction
        FOREIGN KEY (transaction_id)
        REFERENCES production.transactions(transaction_id),
    CONSTRAINT fk_tx_items_product
        FOREIGN KEY (product_id)
        REFERENCES production.products(product_id)
);
CREATE INDEX IF NOT EXISTS idx_tx_items_txid
    ON production.transaction_items(transaction_id);
CREATE INDEX IF NOT EXISTS idx_tx_items_productid
    ON production.transaction_items(product_id);
