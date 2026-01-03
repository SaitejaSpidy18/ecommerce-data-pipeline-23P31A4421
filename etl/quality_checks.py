import json
import os
import time

from etl.db_utils import db_cursor

REPORTS_DIR = "data/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


def run_query_single_value(sql: str):
    with db_cursor() as cur:
        cur.execute(sql)
        return cur.fetchone()[0]


def check_table_not_empty(schema_table: str):
    return run_query_single_value(f"SELECT COUNT(*) FROM {schema_table};") > 0


def check_pk_uniqueness(schema_table: str, pk_column: str):
    total = run_query_single_value(f"SELECT COUNT(*) FROM {schema_table};")
    distinct_pk = run_query_single_value(
        f"SELECT COUNT(DISTINCT {pk_column}) FROM {schema_table};"
    )
    return total == distinct_pk


def run_quality_checks():
    start = time.time()
    results = {}

    # Example checks on production tables
    checks = [
        ("production.customers", "customer_id"),
        ("production.products", "product_id"),
        ("production.transactions", "transaction_id"),
        ("production.transaction_items", "transaction_item_id"),
    ]

    for table, pk in checks:
        table_result = {}
        table_result["not_empty"] = check_table_not_empty(table)
        table_result["pk_unique"] = check_pk_uniqueness(table, pk)
        results[table] = table_result

    # Simple score: percentage of passed checks
    total_checks = sum(len(v) for v in results.values())
    passed_checks = sum(sum(1 for ok in v.values() if ok) for v in results.values())
    score = passed_checks / total_checks if total_checks else 0.0

    end = time.time()
    report = {
        "status": "success",
        "duration_seconds": end - start,
        "score": score,
        "details": results,
    }

    with open(os.path.join(REPORTS_DIR, "quality_report.json"), "w") as f:
        json.dump(report, f, indent=2)

    return report
