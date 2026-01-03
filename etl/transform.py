import json
import os
import time

from etl.db_utils import db_cursor

REPORTS_DIR = "data/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


def copy_staging_to_production():
    with db_cursor(commit=True) as cur:
        # customers
        cur.execute("TRUNCATE TABLE production.customers;")
        cur.execute("""
            INSERT INTO production.customers (customer_id, first_name, last_name, email, signup_date, country)
            SELECT DISTINCT customer_id, first_name, last_name, email, signup_date, country
            FROM staging.customers;
        """)

        # products
        cur.execute("TRUNCATE TABLE production.products;")
        cur.execute("""
            INSERT INTO production.products (product_id, product_name, category, price, is_active)
            SELECT DISTINCT product_id, product_name, category, price, is_active
            FROM staging.products;
        """)

        # transactions
        cur.execute("TRUNCATE TABLE production.transactions;")
        cur.execute("""
            INSERT INTO production.transactions (transaction_id, customer_id, transaction_ts, payment_method, currency)
            SELECT DISTINCT transaction_id, customer_id, transaction_ts, payment_method, currency
            FROM staging.transactions;
        """)

        # transaction_items
        cur.execute("TRUNCATE TABLE production.transaction_items;")
        cur.execute("""
            INSERT INTO production.transaction_items (transaction_item_id, transaction_id, product_id, quantity)
            SELECT DISTINCT transaction_item_id, transaction_id, product_id, quantity
            FROM staging.transaction_items;
        """)


def load_dim_date():
    with db_cursor(commit=True) as cur:
        cur.execute("TRUNCATE TABLE warehouse.dim_date;")
        cur.execute("""
            INSERT INTO warehouse.dim_date (
                date_key, date_value, day_of_week, day_name,
                month, month_name, quarter, year
            )
            SELECT
                DISTINCT
                CAST(TO_CHAR(transaction_ts::date, 'YYYYMMDD') AS INTEGER) AS date_key,
                transaction_ts::date AS date_value,
                EXTRACT(ISODOW FROM transaction_ts) AS day_of_week,
                TO_CHAR(transaction_ts, 'Day') AS day_name,
                EXTRACT(MONTH FROM transaction_ts) AS month,
                TO_CHAR(transaction_ts, 'Month') AS month_name,
                EXTRACT(QUARTER FROM transaction_ts) AS quarter,
                EXTRACT(YEAR FROM transaction_ts) AS year
            FROM production.transactions;
        """)


def load_dim_customer_scd2():
    # For first version, just rebuild from scratch (simple SCD2)
    with db_cursor(commit=True) as cur:
        cur.execute("TRUNCATE TABLE warehouse.dim_customer;")
        cur.execute("""
            INSERT INTO warehouse.dim_customer (
                customer_id, first_name, last_name, email, country, signup_date,
                is_current, valid_from, valid_to
            )
            SELECT
                c.customer_id, c.first_name, c.last_name, c.email, c.country,
                c.signup_date::date,
                TRUE AS is_current,
                NOW() AS valid_from,
                NULL::timestamp AS valid_to
            FROM production.customers c;
        """)


def load_dim_product_scd2():
    with db_cursor(commit=True) as cur:
        cur.execute("TRUNCATE TABLE warehouse.dim_product;")
        cur.execute("""
            INSERT INTO warehouse.dim_product (
                product_id, product_name, category, price, is_active,
                is_current, valid_from, valid_to
            )
            SELECT
                p.product_id, p.product_name, p.category, p.price, p.is_active,
                TRUE AS is_current,
                NOW() AS valid_from,
                NULL::timestamp AS valid_to
            FROM production.products p;
        """)


def load_fact_sales():
    with db_cursor(commit=True) as cur:
        cur.execute("TRUNCATE TABLE warehouse.fact_sales;")
        cur.execute("""
            INSERT INTO warehouse.fact_sales (
                transaction_id, transaction_item_id, date_key, customer_sk, product_sk,
                quantity, unit_price, total_amount, payment_method, currency
            )
            SELECT
                ti.transaction_id,
                ti.transaction_item_id,
                CAST(TO_CHAR(t.transaction_ts::date, 'YYYYMMDD') AS INTEGER) AS date_key,
                dc.customer_sk,
                dp.product_sk,
                ti.quantity,
                p.price AS unit_price,
                (ti.quantity * p.price) AS total_amount,
                t.payment_method,
                t.currency
            FROM production.transaction_items ti
            JOIN production.transactions t
                ON ti.transaction_id = t.transaction_id
            JOIN production.products p
                ON ti.product_id = p.product_id
            JOIN warehouse.dim_customer dc
                ON dc.customer_id = t.customer_id AND dc.is_current = TRUE
            JOIN warehouse.dim_product dp
                ON dp.product_id = ti.product_id AND dp.is_current = TRUE;
        """)


def run_transformations():
    start = time.time()

    copy_staging_to_production()
    load_dim_date()
    load_dim_customer_scd2()
    load_dim_product_scd2()
    load_fact_sales()

    end = time.time()
    report = {
        "status": "success",
        "duration_seconds": end - start,
    }

    with open(os.path.join(REPORTS_DIR, "transformation_summary.json"), "w") as f:
        json.dump(report, f, indent=2)

    return report
