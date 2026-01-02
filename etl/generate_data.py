import os
import random
from datetime import datetime, timedelta

import pandas as pd

RAW_DIR = "data/raw"
os.makedirs(RAW_DIR, exist_ok=True)


def generate_customers(n_customers: int = 1000) -> pd.DataFrame:
    customers = []
    for i in range(1, n_customers + 1):
        customers.append(
            {
                "customer_id": i,
                "first_name": f"First{i}",
                "last_name": f"Last{i}",
                "email": f"customer{i}@example.com",
                "signup_date": datetime(2024, 1, 1)
                + timedelta(days=random.randint(0, 364)),
                "country": random.choice(["IN", "US", "UK", "DE", "FR"]),
            }
        )
    return pd.DataFrame(customers)


def generate_products(n_products: int = 200) -> pd.DataFrame:
    products = []
    for i in range(1, n_products + 1):
        products.append(
            {
                "product_id": i,
                "product_name": f"Product {i}",
                "category": random.choice(
                    ["Electronics", "Clothing", "Books", "Home", "Grocery"]
                ),
                "price": round(random.uniform(5, 500), 2),
                "is_active": random.choice([True, True, True, False]),
            }
        )
    return pd.DataFrame(products)


def generate_transactions(
    n_transactions: int = 5000, n_customers: int = 1000
) -> pd.DataFrame:
    transactions = []
    base_date = datetime(2024, 1, 1)
    for i in range(1, n_transactions + 1):
        txn_date = base_date + timedelta(days=random.randint(0, 364))
        transactions.append(
            {
                "transaction_id": i,
                "customer_id": random.randint(1, n_customers),
                "transaction_ts": txn_date,
                "payment_method": random.choice(
                    ["CARD", "UPI", "NETBANKING", "COD"]
                ),
                "currency": "INR",
            }
        )
    return pd.DataFrame(transactions)


def generate_transaction_items(
    n_transactions: int = 5000, n_products: int = 200
) -> pd.DataFrame:
    items = []
    item_id = 1
    for txn_id in range(1, n_transactions + 1):
        for _ in range(random.randint(1, 5)):
            product_id = random.randint(1, n_products)
            quantity = random.randint(1, 3)
            items.append(
                {
                    "transaction_item_id": item_id,
                    "transaction_id": txn_id,
                    "product_id": product_id,
                    "quantity": quantity,
                }
            )
            item_id += 1
    return pd.DataFrame(items)


def main():
    random.seed(42)
    customers_df = generate_customers()
    products_df = generate_products()
    transactions_df = generate_transactions()
    items_df = generate_transaction_items()

    customers_df.to_csv(os.path.join(RAW_DIR, "customers.csv"), index=False)
    products_df.to_csv(os.path.join(RAW_DIR, "products.csv"), index=False)
    transactions_df.to_csv(os.path.join(RAW_DIR, "transactions.csv"), index=False)
    items_df.to_csv(os.path.join(RAW_DIR, "transaction_items.csv"), index=False)

    print("Raw data generated in", RAW_DIR)


if __name__ == "__main__":
    main()
