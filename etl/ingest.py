import json
import os
import time

import pandas as pd

from etl.db_utils import db_cursor

RAW_DIR = "data/raw"
REPORTS_DIR = "data/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


def load_csv_to_table(csv_path: str, table_name: str, columns: list[str]):
    df = pd.read_csv(csv_path)
    df = df[columns]

    # Ensure pure Python types (avoid numpy.int64 issues)
    df = df.where(pd.notnull(df), None)
    records = [tuple(row) for row in df.astype(object).to_numpy()]

    placeholders = ", ".join(["%s"] * len(columns))
    col_list = ", ".join(columns)
    insert_sql = f"INSERT INTO {table_name} ({col_list}) VALUES ({placeholders})"

    with db_cursor(commit=True) as cur:
        cur.execute(f"TRUNCATE TABLE {table_name};")
        cur.executemany(insert_sql, records)


def run_ingestion():
    start = time.time()
    stats = {}

    load_csv_to_table(
        os.path.join(RAW_DIR, "customers.csv"),
        "staging.customers",
        ["customer_id", "first_name", "last_name", "email", "signup_date", "country"],
    )
    stats["customers_rows"] = sum(1 for _ in open(os.path.join(RAW_DIR, "customers.csv"))) - 1

    load_csv_to_table(
        os.path.join(RAW_DIR, "products.csv"),
        "staging.products",
        ["product_id", "product_name", "category", "price", "is_active"],
    )
    stats["products_rows"] = sum(1 for _ in open(os.path.join(RAW_DIR, "products.csv"))) - 1

    load_csv_to_table(
        os.path.join(RAW_DIR, "transactions.csv"),
        "staging.transactions",
        ["transaction_id", "customer_id", "transaction_ts", "payment_method", "currency"],
    )
    stats["transactions_rows"] = sum(1 for _ in open(os.path.join(RAW_DIR, "transactions.csv"))) - 1

    load_csv_to_table(
        os.path.join(RAW_DIR, "transaction_items.csv"),
        "staging.transaction_items",
        ["transaction_item_id", "transaction_id", "product_id", "quantity"],
    )
    stats["transaction_items_rows"] = sum(1 for _ in open(os.path.join(RAW_DIR, "transaction_items.csv"))) - 1

    end = time.time()
    report = {
        "status": "success",
        "duration_seconds": end - start,
        "tables": stats,
    }

    with open(os.path.join(REPORTS_DIR, "ingestion_summary.json"), "w") as f:
        json.dump(report, f, indent=2)

    return report
