CREATE TABLE IF NOT EXISTS production.transactions (
    transaction_id  INTEGER PRIMARY KEY,
    customer_id     INTEGER NOT NULL,
    transaction_ts  TIMESTAMP NOT NULL,
    payment_method  TEXT NOT NULL,
    currency        TEXT NOT NULL,
    CONSTRAINT fk_transactions_customer
        FOREIGN KEY (customer_id)
        REFERENCES production.customers(customer_id)
);
CREATE INDEX IF NOT EXISTS idx_transactions_customer
    ON production.transactions(customer_id);
CREATE INDEX IF NOT EXISTS idx_transactions_ts
    ON production.transactions(transaction_ts);
