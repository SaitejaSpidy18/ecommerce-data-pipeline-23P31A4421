from etl.generate_data import (
    generate_customers,
    generate_products,
    generate_transactions,
    generate_transaction_items,
)


def test_generate_customers_shape():
    df = generate_customers(10)
    assert len(df) == 10
    assert {"customer_id", "email"}.issubset(df.columns)


def test_generate_products_shape():
    df = generate_products(5)
    assert len(df) == 5
    assert {"product_id", "price"}.issubset(df.columns)
