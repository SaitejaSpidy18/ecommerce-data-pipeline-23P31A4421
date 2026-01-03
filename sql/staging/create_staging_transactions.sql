CREATE TABLE IF NOT EXISTS staging.transactions (
    transaction_id  INTEGER,
    customer_id     INTEGER,
    transaction_ts  TIMESTAMP,
    payment_method  TEXT,
    currency        TEXT
);
