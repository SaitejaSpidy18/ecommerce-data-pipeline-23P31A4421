CREATE SCHEMA IF NOT EXISTS staging;

CREATE TABLE IF NOT EXISTS staging.customers (
    customer_id      INTEGER,
    first_name       TEXT,
    last_name        TEXT,
    email            TEXT,
    signup_date      TIMESTAMP,
    country          TEXT
);
