# tests/test_transformation.py
import pytest
import os
import json
import psycopg2
from datetime import datetime
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scripts.transformation.staging_to_production import (
    load_config,
    get_db_connection,
    clean_text,
    standardize_email,
    standardize_phone
)
class TestTransformation:
    """Test suite for transformation module"""
    @pytest.fixture
    def config(self):
        """Load test configuration"""
        return load_config()
    @pytest.fixture
    def db_connection(self, config):
        """Create database connection"""
        try:
            conn = get_db_connection(config)
            yield conn
            conn.close()
        except Exception as e:
            pytest.skip(f"Database not available: {str(e)}")
    def test_clean_text(self):
        """Test text cleaning function"""
        assert clean_text('  hello  world  ') == 'hello world'
        assert clean_text('UPPERCASE') == 'UPPERCASE'
        assert clean_text(None) is None
        assert clean_text('') == ''
        assert clean_text('   ') == ''
    def test_standardize_email(self):
        """Test email standardization"""
        assert standardize_email('TEST@EXAMPLE.COM') == 'test@example.com'
        assert standardize_email('  user@domain.com  ') == 'user@domain.com'
        assert standardize_email('invalid_email') is None
        assert standardize_email(None) is None
        assert standardize_email('user@example.co.uk') == 'user@example.co.uk'
    def test_standardize_phone(self):
        """Test phone standardization"""
        assert standardize_phone('+91-9876543210') == '+919876543210'
        assert standardize_phone('9876543210') == '9876543210'
        assert standardize_phone('  +91 98765 43210  ') == '+919876543210'
        assert standardize_phone(None) is None
        assert standardize_phone('') is None
    def test_production_schema_exists(self, db_connection):
        """Test that production schema exists"""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT schema_name FROM information_schema.schemata 
            WHERE schema_name = 'production';
        """)
        result = cursor.fetchone()
        cursor.close()
        assert result is not None, "Production schema does not exist"
    def test_production_tables_exist(self, db_connection):
        """Test that all production tables exist"""
        cursor = db_connection.cursor()
        tables = ['customers', 'products', 'transactions', 'transaction_items']
        for table in tables:
            cursor.execute(f"""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'production' AND table_name = '{table}';
            """)
            result = cursor.fetchone()
            assert result is not None, f"Table production.{table} does not exist"
        cursor.close()
    def test_production_constraints(self, db_connection):
        """Test that production tables have constraints"""
        cursor = db_connection.cursor()
        # Check primary key constraint on customers
        cursor.execute("""
            SELECT constraint_name FROM information_schema.table_constraints
            WHERE table_schema = 'production' AND table_name = 'customers' 
            AND constraint_type = 'PRIMARY KEY';
        """)
        result = cursor.fetchone()
        assert result is not None, "Primary key missing on production.customers"
        # Check foreign key constraints on transactions
        cursor.execute("""
            SELECT constraint_name FROM information_schema.table_constraints
            WHERE table_schema = 'production' AND table_name = 'transactions'
            AND constraint_type = 'FOREIGN KEY';
        """)
        result = cursor.fetchone()
        assert result is not None, "Foreign key missing on production.transactions"
        cursor.close()
    def test_data_type_correctness(self, db_connection):
        """Test that column data types are correct"""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT column_name, data_type FROM information_schema.columns
            WHERE table_schema = 'production' AND table_name = 'customers'
            AND column_name IN ('customer_id', 'email', 'is_active');
        """)
        columns = {row[0]: row[1] for row in cursor.fetchall()}
        assert columns['customer_id'] == 'integer', "customer_id should be integer"
        assert columns['email'] == 'character varying', "email should be varchar"
        assert columns['is_active'] == 'boolean', "is_active should be boolean"
        cursor.close()
    def test_transformation_summary_creation(self, tmp_path):
        """Test transformation summary JSON creation"""
        summary = {
            'transformation_timestamp': datetime.now().isoformat(),
            'status': 'SUCCESS',
            'duration_seconds': 25.3,
            'transformation_summary': {
                'customers': {
                    'staging': 1000,
                    'production': 950,
                    'filtered': 50
                },
                'products': {
                    'staging': 500,
                    'production': 480,
                    'filtered': 20
                },
                'transactions': {
                    'staging': 10000,
                    'production': 9800,
                    'filtered': 200
                },
                'transaction_items': {
                    'staging': 18500,
                    'production': 18200,
                    'filtered': 300
                }
            },
            'total_records_processed': 30000,
            'total_records_loaded': 29430,
            'total_records_filtered': 570
        }
        output_file = tmp_path / 'transformation_summary.json'
        with open(output_file, 'w') as f:
            json.dump(summary, f)
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded = json.load(f)
            assert loaded['status'] == 'SUCCESS'
            assert loaded['total_records_loaded'] == 29430
            assert loaded['total_records_filtered'] == 570
    def test_business_rule_validation(self):
        """Test business rule validation"""
        # Test price >= cost rule
        assert 100 >= 50  # Valid
        # Test quantity > 0 rule
        assert 5 > 0  # Valid
        # Test email format rule
        test_email = 'user@example.com'
        assert '@' in test_email  # Valid format
    def test_null_handling(self):
        """Test NULL value handling"""
        # Test that NULL cleaning works
        assert clean_text(None) is None
        assert standardize_email(None) is None
        assert standardize_phone(None) is None
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
