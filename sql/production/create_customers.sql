CREATE SCHEMA IF NOT EXISTS production;

CREATE TABLE IF NOT EXISTS production.customers (
    customer_id   INTEGER PRIMARY KEY,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    signup_date   TIMESTAMP NOT NULL,
    country       TEXT NOT NULL
);
