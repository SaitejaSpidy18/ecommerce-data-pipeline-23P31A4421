# scripts/ingestion/ingest_to_staging.py

import os
import json
import csv
import logging
from datetime import datetime
import yaml
import psycopg2
from psycopg2.extras import execute_values
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration from config/config.yaml"""
    config_path = "config/config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_db_connection(config):
    """Create PostgreSQL database connection"""
    try:
        conn = psycopg2.connect(
            host=config['database']['host'],
            port=config['database']['port'],
            database=config['database']['name'],
            user=config['database']['user'],
            password=config['database']['password'],
            connect_timeout=config['database']['connect_timeout_seconds']
        )
        logger.info("✓ Database connection established")
        return conn
    except psycopg2.Error as e:
        logger.error(f"✗ Failed to connect to database: {str(e)}")
        raise

def truncate_staging_tables(conn, schema='staging'):
    """Truncate all staging tables before reload"""
    try:
        cursor = conn.cursor()
        tables = ['customers', 'products', 'transactions', 'transaction_items']
        
        for table in tables:
            cursor.execute(f"TRUNCATE TABLE {schema}.{table} CASCADE;")
            logger.info(f"Truncated {schema}.{table}")
        
        conn.commit()
        cursor.close()
        logger.info("✓ All staging tables truncated")
    except psycopg2.Error as e:
        conn.rollback()
        logger.error(f"✗ Error truncating staging tables: {str(e)}")
        raise

def ingest_customers(conn, csv_file, config):
    """Ingest customers data from CSV to staging.customers"""
    logger.info(f"Ingesting customers from {csv_file}...")
    
    try:
        cursor = conn.cursor()
        batch_size = config['pipeline']['batch_size']
        rows_loaded = 0
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            
            for row in reader:
                batch.append((
                    int(row['customer_id']),
                    row['first_name'],
                    row['last_name'],
                    row['email'],
                    row['phone'],
                    row['address'],
                    row['city'],
                    row['state'],
                    row['postal_code'],
                    row['country'],
                    row['signup_date'],
                    row['is_active'].lower() == 'true'
                ))
                
                if len(batch) >= batch_size:
                    execute_values(
                        cursor,
                        "INSERT INTO staging.customers (customer_id, first_name, last_name, email, phone, address, city, state, postal_code, country, signup_date, is_active) VALUES %s",
                        batch
                    )
                    rows_loaded += len(batch)
                    batch = []
            
            # Insert remaining batch
            if batch:
                execute_values(
                    cursor,
                    "INSERT INTO staging.customers (customer_id, first_name, last_name, email, phone, address, city, state, postal_code, country, signup_date, is_active) VALUES %s",
                    batch
                )
                rows_loaded += len(batch)
        
        conn.commit()
        cursor.close()
        logger.info(f"✓ Loaded {rows_loaded} customers")
        return rows_loaded
        
    except Exception as e:
        conn.rollback()
        logger.error(f"✗ Error ingesting customers: {str(e)}")
        raise

def ingest_products(conn, csv_file, config):
    """Ingest products data from CSV to staging.products"""
    logger.info(f"Ingesting products from {csv_file}...")
    
    try:
        cursor = conn.cursor()
        batch_size = config['pipeline']['batch_size']
        rows_loaded = 0
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            
            for row in reader:
                batch.append((
                    int(row['product_id']),
                    row['product_name'],
                    row['category'],
                    float(row['cost']),
                    float(row['price']),
                    int(row['stock_quantity']),
                    row['is_active'].lower() == 'true',
                    row['created_date']
                ))
                
                if len(batch) >= batch_size:
                    execute_values(
                        cursor,
                        "INSERT INTO staging.products (product_id, product_name, category, cost, price, stock_quantity, is_active, created_date) VALUES %s",
                        batch
                    )
                    rows_loaded += len(batch)
                    batch = []
            
            # Insert remaining batch
            if batch:
                execute_values(
                    cursor,
                    "INSERT INTO staging.products (product_id, product_name, category, cost, price, stock_quantity, is_active, created_date) VALUES %s",
                    batch
                )
                rows_loaded += len(batch)
        
        conn.commit()
        cursor.close()
        logger.info(f"✓ Loaded {rows_loaded} products")
        return rows_loaded
        
    except Exception as e:
        conn.rollback()
        logger.error(f"✗ Error ingesting products: {str(e)}")
        raise

def ingest_transactions(conn, csv_file, config):
    """Ingest transactions data from CSV to staging.transactions"""
    logger.info(f"Ingesting transactions from {csv_file}...")
    
    try:
        cursor = conn.cursor()
        batch_size = config['pipeline']['batch_size']
        rows_loaded = 0
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            
            for row in reader:
                batch.append((
                    int(row['transaction_id']),
                    int(row['customer_id']),
                    row['transaction_date'],
                    row['payment_method'],
                    float(row['total_amount']),
                    row['transaction_status']
                ))
                
                if len(batch) >= batch_size:
                    execute_values(
                        cursor,
                        "INSERT INTO staging.transactions (transaction_id, customer_id, transaction_date, payment_method, total_amount, transaction_status) VALUES %s",
                        batch
                    )
                    rows_loaded += len(batch)
                    batch = []
            
            # Insert remaining batch
            if batch:
                execute_values(
                    cursor,
                    "INSERT INTO staging.transactions (transaction_id, customer_id, transaction_date, payment_method, total_amount, transaction_status) VALUES %s",
                    batch
                )
                rows_loaded += len(batch)
        
        conn.commit()
        cursor.close()
        logger.info(f"✓ Loaded {rows_loaded} transactions")
        return rows_loaded
        
    except Exception as e:
        conn.rollback()
        logger.error(f"✗ Error ingesting transactions: {str(e)}")
        raise

def ingest_transaction_items(conn, csv_file, config):
    """Ingest transaction items data from CSV to staging.transaction_items"""
    logger.info(f"Ingesting transaction items from {csv_file}...")
    
    try:
        cursor = conn.cursor()
        batch_size = config['pipeline']['batch_size']
        rows_loaded = 0
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            batch = []
            
            for row in reader:
                batch.append((
                    int(row['item_id']),
                    int(row['transaction_id']),
                    int(row['product_id']),
                    int(row['quantity']),
                    float(row['unit_price']),
                    float(row['line_total'])
                ))
                
                if len(batch) >= batch_size:
                    execute_values(
                        cursor,
                        "INSERT INTO staging.transaction_items (item_id, transaction_id, product_id, quantity, unit_price, line_total) VALUES %s",
                        batch
                    )
                    rows_loaded += len(batch)
                    batch = []
            
            # Insert remaining batch
            if batch:
                execute_values(
                    cursor,
                    "INSERT INTO staging.transaction_items (item_id, transaction_id, product_id, quantity, unit_price, line_total) VALUES %s",
                    batch
                )
                rows_loaded += len(batch)
        
        conn.commit()
        cursor.close()
        logger.info(f"✓ Loaded {rows_loaded} transaction items")
        return rows_loaded
        
    except Exception as e:
        conn.rollback()
        logger.error(f"✗ Error ingesting transaction items: {str(e)}")
        raise

def validate_ingestion(conn):
    """Validate data ingestion - check row counts"""
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM staging.customers;")
        customer_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM staging.products;")
        product_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM staging.transactions;")
        transaction_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM staging.transaction_items;")
        item_count = cursor.fetchone()[0]
        
        cursor.close()
        
        validation = {
            'customers': customer_count,
            'products': product_count,
            'transactions': transaction_count,
            'transaction_items': item_count
        }
        
        logger.info("✓ Ingestion validation:")
        logger.info(f"  - Customers: {customer_count}")
        logger.info(f"  - Products: {product_count}")
        logger.info(f"  - Transactions: {transaction_count}")
        logger.info(f"  - Transaction Items: {item_count}")
        
        return validation
        
    except psycopg2.Error as e:
        logger.error(f"✗ Error validating ingestion: {str(e)}")
        raise

def create_ingestion_summary(output_dir, validation, duration_seconds):
    """Create ingestion summary JSON"""
    summary = {
        'ingestion_timestamp': datetime.now().isoformat(),
        'status': 'SUCCESS',
        'duration_seconds': duration_seconds,
        'row_counts': validation,
        'total_rows_loaded': sum(validation.values())
    }
    
    output_file = os.path.join(output_dir, 'ingestion_summary.json')
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    logger.info(f"✓ Ingestion summary saved to {output_file}")
    return summary

def main():
    """Main execution"""
    print("\n" + "="*60)
    print("E-Commerce Data Ingestion Pipeline")
    print("="*60 + "\n")
    
    start_time = datetime.now()
    
    try:
        # Load config
        config = load_config()
        logger.info("✓ Configuration loaded")
        
        # Get database connection
        conn = get_db_connection(config)
        
        # Truncate staging tables
        truncate_staging_tables(conn)
        
        # Get raw data directory
        raw_dir = config['paths']['data_raw']
        
        # Ingest all tables
        customer_count = ingest_customers(conn, os.path.join(raw_dir, 'customers.csv'), config)
        product_count = ingest_products(conn, os.path.join(raw_dir, 'products.csv'), config)
        transaction_count = ingest_transactions(conn, os.path.join(raw_dir, 'transactions.csv'), config)
        item_count = ingest_transaction_items(conn, os.path.join(raw_dir, 'transaction_items.csv'), config)
        
        # Validate ingestion
        validation = validate_ingestion(conn)
        
        # Create summary
        duration = (datetime.now() - start_time).total_seconds()
        processed_dir = config['paths']['data_staging']
        Path(processed_dir).mkdir(parents=True, exist_ok=True)
        summary = create_ingestion_summary(processed_dir, validation, duration)
        
        # Close connection
        conn.close()
        
        # Print summary
        print("\n" + "="*60)
        print("Ingestion Completed Successfully")
        print("="*60)
        print(f"Duration: {duration:.2f} seconds")
        print(f"Total Rows Loaded: {summary['total_rows_loaded']}")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Ingestion pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
