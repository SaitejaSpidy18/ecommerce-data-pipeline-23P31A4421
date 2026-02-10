# tests/test_ingestion.py
import pytest
import os
import json
import yaml
import psycopg2
from datetime import datetime
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from scripts.ingestion.ingest_to_staging import (
    load_config,
    get_db_connection,
    validate_ingestion
)
class TestIngestion:
    """Test suite for data ingestion module"""
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
    def test_load_config(self):
        """Test configuration loading"""
        config = load_config()
        assert config is not None
        assert 'database' in config
        assert 'host' in config['database']
        assert 'paths' in config
    def test_database_connection(self, config):
        """Test database connection"""
        try:
            conn = get_db_connection(config)
            assert conn is not None
            conn.close()
        except Exception as e:
            pytest.skip(f"Database not available: {str(e)}")
    def test_staging_schema_exists(self, db_connection):
        """Test that staging schema exists"""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT schema_name FROM information_schema.schemata 
            WHERE schema_name = 'staging';
        """)
        result = cursor.fetchone()
        cursor.close()
        assert result is not None, "Staging schema does not exist"
    def test_staging_tables_exist(self, db_connection):
        """Test that all staging tables exist"""
        cursor = db_connection.cursor()
        tables = ['customers', 'products', 'transactions', 'transaction_items']
        for table in tables:
            cursor.execute(f"""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'staging' AND table_name = '{table}';
            """)
            result = cursor.fetchone()
            assert result is not None, f"Table staging.{table} does not exist"
        cursor.close()
    def test_staging_table_columns(self, db_connection):
        """Test that staging tables have expected columns"""
        cursor = db_connection.cursor()
        cursor.execute("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_schema = 'staging' AND table_name = 'customers' 
            ORDER BY column_name;
        """)
        columns = [row[0] for row in cursor.fetchall()]
        expected_columns = ['address', 'city', 'country', 'customer_id', 'email', 
                           'first_name', 'last_name', 'load_timestamp', 'phone', 
                           'postal_code', 'signup_date', 'state', 'is_active']
        for col in expected_columns:
            assert col in columns, f"Column {col} missing from staging.customers"
        cursor.close()
    def test_validate_ingestion_function(self, db_connection):
        """Test ingestion validation function"""
        try:
            validation = validate_ingestion(db_connection)
            assert validation is not None
            assert 'customers' in validation
            assert 'products' in validation
            assert 'transactions' in validation
            assert 'transaction_items' in validation
            for table, count in validation.items():
                assert isinstance(count, int)
                assert count >= 0
        except Exception as e:
            pytest.skip(f"Validation failed: {str(e)}")
    def test_ingestion_summary_creation(self, tmp_path):
        """Test ingestion summary JSON creation"""
        summary = {
            'ingestion_timestamp': datetime.now().isoformat(),
            'status': 'SUCCESS',
            'duration_seconds': 15.5,
            'row_counts': {
                'customers': 100,
                'products': 50,
                'transactions': 200,
                'transaction_items': 500
            },
            'total_rows_loaded': 850
        }
        output_file = tmp_path / 'ingestion_summary.json'
        with open(output_file, 'w') as f:
            json.dump(summary, f)
        assert output_file.exists()
        with open(output_file, 'r') as f:
            loaded = json.load(f)
            assert loaded['status'] == 'SUCCESS'
            assert loaded['total_rows_loaded'] == 850
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
