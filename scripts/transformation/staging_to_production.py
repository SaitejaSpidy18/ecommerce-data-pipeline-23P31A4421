# scripts/transformation/staging_to_production.py
import os
import json
import logging
from datetime import datetime
import yaml
import psycopg2
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
def clean_text(text):
    """Clean and normalize text data"""
    if text is None:
        return None
    text = str(text).strip()
    text = ' '.join(text.split())  # Remove extra whitespace
    return text
def standardize_email(email):
    """Standardize email format"""
    if email is None:
        return None
    email = email.strip().lower()
    return email if '@' in email else None
def standardize_phone(phone):
    """Standardize phone format"""
    if phone is None:
        return None
    # Remove non-numeric characters except +
    phone = ''.join(c for c in str(phone) if c.isdigit() or c == '+')
    return phone if phone else None
def transform_customers(conn):
    """Transform and load customers from staging to production"""
    logger.info("Transforming customers...")
    try:
        cursor = conn.cursor()
        # Truncate production table for idempotency
        cursor.execute("TRUNCATE TABLE production.customers;")
        # Transform and insert customers
        cursor.execute("""
            INSERT INTO production.customers (
                customer_id, first_name, last_name, email, phone, address,
                city, state, postal_code, country, signup_date, is_active
            )
            SELECT
                customer_id,
                TRIM(first_name) as first_name,
                TRIM(last_name) as last_name,
                LOWER(TRIM(email)) as email,
                REGEXP_REPLACE(phone, '[^0-9+]', '', 'g') as phone,
                TRIM(address) as address,
                TRIM(city) as city,
                TRIM(state) as state,
                TRIM(postal_code) as postal_code,
                COALESCE(NULLIF(TRIM(country), ''), 'India') as country,
                signup_date,
                COALESCE(is_active, TRUE) as is_active
            FROM staging.customers
            WHERE customer_id IS NOT NULL
                AND email IS NOT NULL
                AND email LIKE '%@%'
                AND first_name IS NOT NULL
                AND last_name IS NOT NULL;
        """)
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        logger.info(f"✓ Transformed and loaded {rows_affected} customers")
        return rows_affected
    except Exception as e:
        conn.rollback()
        logger.error(f"✗ Error transforming customers: {str(e)}")
        raise
def transform_products(conn):
    """Transform and load products from staging to production"""
    logger.info("Transforming products...")
    try:
        cursor = conn.cursor()
        # Truncate production table for idempotency
        cursor.execute("TRUNCATE TABLE production.products;")
        # Transform and insert products
        cursor.execute("""
            INSERT INTO production.products (
                product_id, product_name, category, cost, price,
                stock_quantity, is_active, created_date
            )
            SELECT
                product_id,
                TRIM(product_name) as product_name,
                TRIM(category) as category,
                cost,
                price,
                GREATEST(stock_quantity, 0) as stock_quantity,
                COALESCE(is_active, TRUE) as is_active,
                created_date
            FROM staging.products
            WHERE product_id IS NOT NULL
                AND product_name IS NOT NULL
                AND category IS NOT NULL
                AND cost > 0
                AND price > 0
                AND price >= cost;
        """)
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        logger.info(f"✓ Transformed and loaded {rows_affected} products")
        return rows_affected
    except Exception as e:
        conn.rollback()
        logger.error(f"✗ Error transforming products: {str(e)}")
        raise
def transform_transactions(conn):
    """Transform and load transactions from staging to production"""
    logger.info("Transforming transactions...")
    try:
        cursor = conn.cursor()
        # Truncate production table for idempotency
        cursor.execute("TRUNCATE TABLE production.transactions CASCADE;")
        # Transform and insert transactions
        cursor.execute("""
            INSERT INTO production.transactions (
                transaction_id, customer_id, transaction_date, payment_method,
                total_amount, transaction_status
            )
            SELECT
                t.transaction_id,
                t.customer_id,
                t.transaction_date,
                CASE 
                    WHEN TRIM(t.payment_method) IN ('Credit Card', 'Debit Card', 'UPI', 'Net Banking', 'Cash')
                    THEN TRIM(t.payment_method)
                    ELSE 'Unknown'
                END as payment_method,
                GREATEST(t.total_amount, 0) as total_amount,
                CASE 
                    WHEN TRIM(t.transaction_status) IN ('Completed', 'Pending', 'Failed')
                    THEN TRIM(t.transaction_status)
                    ELSE 'Unknown'
                END as transaction_status
            FROM staging.transactions t
            WHERE t.transaction_id IS NOT NULL
                AND t.customer_id IS NOT NULL
                AND t.transaction_date IS NOT NULL
                AND t.total_amount > 0
                AND EXISTS (
                    SELECT 1 FROM production.customers c
                    WHERE c.customer_id = t.customer_id
                );
        """)
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        logger.info(f"✓ Transformed and loaded {rows_affected} transactions")
        return rows_affected
    except Exception as e:
        conn.rollback()
        logger.error(f"✗ Error transforming transactions: {str(e)}")
        raise
def transform_transaction_items(conn):
    """Transform and load transaction items from staging to production"""
    logger.info("Transforming transaction items...")
    try:
        cursor = conn.cursor()
        # Truncate production table for idempotency
        cursor.execute("TRUNCATE TABLE production.transaction_items;")
        # Transform and insert transaction items
        cursor.execute("""
            INSERT INTO production.transaction_items (
                item_id, transaction_id, product_id, quantity,
                unit_price, line_total
            )
            SELECT
                ti.item_id,
                ti.transaction_id,
                ti.product_id,
                ti.quantity,
                ti.unit_price,
                ti.quantity * ti.unit_price as line_total
            FROM staging.transaction_items ti
            WHERE ti.item_id IS NOT NULL
                AND ti.transaction_id IS NOT NULL
                AND ti.product_id IS NOT NULL
                AND ti.quantity > 0
                AND ti.unit_price > 0
                AND EXISTS (
                    SELECT 1 FROM production.transactions t
                    WHERE t.transaction_id = ti.transaction_id
                )
                AND EXISTS (
                    SELECT 1 FROM production.products p
                    WHERE p.product_id = ti.product_id
                );
        """)
        rows_affected = cursor.rowcount
        conn.commit()
        cursor.close()
        logger.info(f"✓ Transformed and loaded {rows_affected} transaction items")
        return rows_affected
    except Exception as e:
        conn.rollback()
        logger.error(f"✗ Error transforming transaction items: {str(e)}")
        raise
def calculate_transformation_metrics(conn):
    """Calculate transformation metrics"""
    try:
        cursor = conn.cursor()
        metrics = {}
        # Customer metrics
        cursor.execute("SELECT COUNT(*) FROM staging.customers;")
        staging_customers = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM production.customers;")
        prod_customers = cursor.fetchone()[0]
        metrics['customers'] = {
            'staging': staging_customers,
            'production': prod_customers,
            'filtered': staging_customers - prod_customers
        }
        # Product metrics
        cursor.execute("SELECT COUNT(*) FROM staging.products;")
        staging_products = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM production.products;")
        prod_products = cursor.fetchone()[0]
        metrics['products'] = {
            'staging': staging_products,
            'production': prod_products,
            'filtered': staging_products - prod_products
        }
        # Transaction metrics
        cursor.execute("SELECT COUNT(*) FROM staging.transactions;")
        staging_trans = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM production.transactions;")
        prod_trans = cursor.fetchone()[0]
        metrics['transactions'] = {
            'staging': staging_trans,
            'production': prod_trans,
            'filtered': staging_trans - prod_trans
        }
        # Transaction items metrics
        cursor.execute("SELECT COUNT(*) FROM staging.transaction_items;")
        staging_items = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM production.transaction_items;")
        prod_items = cursor.fetchone()[0]
        metrics['transaction_items'] = {
            'staging': staging_items,
            'production': prod_items,
            'filtered': staging_items - prod_items
        }
        cursor.close()
        return metrics
    except psycopg2.Error as e:
        logger.error(f"✗ Error calculating metrics: {str(e)}")
        raise
def create_transformation_summary(output_dir, metrics, duration_seconds):
    """Create transformation summary JSON"""
    summary = {
        'transformation_timestamp': datetime.now().isoformat(),
        'status': 'SUCCESS',
        'duration_seconds': duration_seconds,
        'transformation_summary': {
            'customers': metrics['customers'],
            'products': metrics['products'],
            'transactions': metrics['transactions'],
            'transaction_items': metrics['transaction_items']
        },
        'total_records_processed': sum(m['staging'] for m in metrics.values()),
        'total_records_loaded': sum(m['production'] for m in metrics.values()),
        'total_records_filtered': sum(m['filtered'] for m in metrics.values())
    }
    output_file = os.path.join(output_dir, 'transformation_summary.json')
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    logger.info(f"✓ Transformation summary saved to {output_file}")
    return summary
def main():
    """Main execution"""
    print("\n" + "="*60)
    print("Staging to Production Transformation Pipeline")
    print("="*60 + "\n")
    start_time = datetime.now()
    try:
        # Load config
        config = load_config()
        logger.info("✓ Configuration loaded")
        # Get database connection
        conn = get_db_connection(config)
        # Transform each table
        customer_count = transform_customers(conn)
        product_count = transform_products(conn)
        transaction_count = transform_transactions(conn)
        item_count = transform_transaction_items(conn)
        # Calculate metrics
        metrics = calculate_transformation_metrics(conn)
        # Create summary
        duration = (datetime.now() - start_time).total_seconds()
        processed_dir = config['paths']['data_processed']
        Path(processed_dir).mkdir(parents=True, exist_ok=True)
        summary = create_transformation_summary(processed_dir, metrics, duration)
        # Close connection
        conn.close()
        # Print summary
        print("\n" + "="*60)
        print("Transformation Completed Successfully")
        print("="*60)
        print(f"Duration: {duration:.2f} seconds")
        print(f"Customers: {metrics['customers']['production']} loaded (filtered: {metrics['customers']['filtered']})")
        print(f"Products: {metrics['products']['production']} loaded (filtered: {metrics['products']['filtered']})")
        print(f"Transactions: {metrics['transactions']['production']} loaded (filtered: {metrics['transactions']['filtered']})")
        print(f"Transaction Items: {metrics['transaction_items']['production']} loaded (filtered: {metrics['transaction_items']['filtered']})")
        print(f"Total Records Loaded: {summary['total_records_loaded']}")
        print("="*60 + "\n")
        return True
    except Exception as e:
        logger.error(f"✗ Transformation pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
