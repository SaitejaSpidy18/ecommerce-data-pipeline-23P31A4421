# tests/test_data_generation.py
import pytest
import os
import json
from pathlib import Path
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scripts.data_generation.generate_data import (
    load_config,
    generate_customers,
    generate_products,
    generate_transactions,
    generate_transaction_items,
    generate_metadata
)
class TestDataGeneration:
    """Test suite for data generation module"""
    @pytest.fixture
    def config(self):
        """Load test configuration"""
        return load_config()
    @pytest.fixture
    def output_dir(self, tmp_path):
        """Create temporary output directory"""
        return str(tmp_path)
    def test_load_config(self):
        """Test configuration loading"""
        config = load_config()
        assert config is not None
        assert 'data_generation' in config
        assert 'num_customers' in config['data_generation']
        assert 'num_products' in config['data_generation']
    def test_generate_customers(self, config, output_dir):
        """Test customer data generation"""
        num_customers = 100
        config['data_generation']['num_customers'] = num_customers
        customers = generate_customers(num_customers, output_dir)
        assert len(customers) == num_customers
        assert all('customer_id' in c for c in customers)
        assert all('email' in c for c in customers)
        assert all('first_name' in c for c in customers)
        assert len(set(c['customer_id'] for c in customers)) == num_customers
        csv_file = os.path.join(output_dir, 'customers.csv')
        assert os.path.exists(csv_file)
    def test_generate_products(self, config, output_dir):
        """Test product data generation"""
        num_products = 50
        products = generate_products(num_products, output_dir)
        assert len(products) == num_products
        assert all('product_id' in p for p in products)
        assert all('product_name' in p for p in products)
        assert all('price' in p for p in products)
        assert all(p['price'] > 0 for p in products)
        assert all(p['price'] >= p['cost'] for p in products)
        csv_file = os.path.join(output_dir, 'products.csv')
        assert os.path.exists(csv_file)
    def test_generate_transactions(self, config, output_dir):
        """Test transaction data generation"""
        num_customers = 50
        num_products = 30
        num_transactions = 100
        customers = generate_customers(num_customers, output_dir)
        products = generate_products(num_products, output_dir)
        transactions = generate_transactions(
            num_transactions,
            customers,
            products,
            '2024-01-01',
            '2024-12-31',
            output_dir
        )
        assert len(transactions) == num_transactions
        assert all('transaction_id' in t for t in transactions)
        assert all('customer_id' in t for t in transactions)
        assert all('transaction_date' in t for t in transactions)
        assert all('total_amount' in t for t in transactions)
        customer_ids = set(c['customer_id'] for c in customers)
        assert all(t['customer_id'] in customer_ids for t in transactions)
        csv_file = os.path.join(output_dir, 'transactions.csv')
        assert os.path.exists(csv_file)
    def test_generate_transaction_items(self, config, output_dir):
        """Test transaction items generation"""
        num_customers = 30
        num_products = 20
        num_transactions = 50
        customers = generate_customers(num_customers, output_dir)
        products = generate_products(num_products, output_dir)
        transactions = generate_transactions(
            num_transactions,
            customers,
            products,
            '2024-01-01',
            '2024-12-31',
            output_dir
        )
        transaction_items = generate_transaction_items(
            transactions,
            products,
            100,
            200,
            output_dir
        )
        assert len(transaction_items) > 0
        assert all('item_id' in ti for ti in transaction_items)
        assert all('transaction_id' in ti for ti in transaction_items)
        assert all('product_id' in ti for ti in transaction_items)
        assert all('quantity' in ti for ti in transaction_items)
        product_ids = set(p['product_id'] for p in products)
        transaction_ids = set(t['transaction_id'] for t in transactions)
        assert all(ti['product_id'] in product_ids for ti in transaction_items)
        assert all(ti['transaction_id'] in transaction_ids for ti in transaction_items)
        csv_file = os.path.join(output_dir, 'transaction_items.csv')
        assert os.path.exists(csv_file)
    def test_generate_metadata(self, config, output_dir):
        """Test metadata generation"""
        num_customers = 20
        num_products = 15
        num_transactions = 30
        customers = generate_customers(num_customers, output_dir)
        products = generate_products(num_products, output_dir)
        transactions = generate_transactions(
            num_transactions,
            customers,
            products,
            '2024-01-01',
            '2024-12-31',
            output_dir
        )
        transaction_items = generate_transaction_items(
            transactions,
            products,
            50,
            100,
            output_dir
        )
        metadata = generate_metadata(output_dir, customers, products, transactions, transaction_items)
        assert metadata is not None
        assert 'generated_at' in metadata
        assert 'generation_summary' in metadata
        assert metadata['generation_summary']['num_customers'] == num_customers
        assert metadata['generation_summary']['num_products'] == num_products
        assert metadata['generation_summary']['num_transactions'] == num_transactions
        json_file = os.path.join(output_dir, 'generation_metadata.json')
        assert os.path.exists(json_file)
        with open(json_file, 'r') as f:
            loaded_metadata = json.load(f)
            assert loaded_metadata['generation_summary']['num_customers'] == num_customers
    def test_data_integrity(self, config, output_dir):
        """Test data integrity constraints"""
        num_customers = 10
        num_products = 10
        num_transactions = 20
        customers = generate_customers(num_customers, output_dir)
        products = generate_products(num_products, output_dir)
        transactions = generate_transactions(
            num_transactions,
            customers,
            products,
            '2024-01-01',
            '2024-12-31',
            output_dir
        )
        transaction_items = generate_transaction_items(
            transactions,
            products,
            20,
            50,
            output_dir
        )
        assert len(set(c['customer_id'] for c in customers)) == len(customers)
        assert len(set(p['product_id'] for p in products)) == len(products)
        assert len(set(t['transaction_id'] for t in transactions)) == len(transactions)
        assert len(set(ti['item_id'] for ti in transaction_items)) == len(transaction_items)
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
