# scripts/quality_checks/validate_data.py
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
def check_completeness(conn, schema='staging'):
    """Check for NULL values in critical columns"""
    logger.info("Checking completeness...")
    issues = []
    try:
        cursor = conn.cursor()
        checks = {
            'customers': ['customer_id', 'email', 'first_name', 'last_name'],
            'products': ['product_id', 'product_name', 'price'],
            'transactions': ['transaction_id', 'customer_id', 'transaction_date', 'total_amount'],
            'transaction_items': ['item_id', 'transaction_id', 'product_id', 'quantity']
        }
        for table, columns in checks.items():
            for col in columns:
                cursor.execute(f"SELECT COUNT(*) FROM {schema}.{table} WHERE {col} IS NULL;")
                null_count = cursor.fetchone()[0]
                if null_count > 0:
                    issues.append(f"{schema}.{table}.{col}: {null_count} NULL values")
                    logger.warning(f"  ⚠ {schema}.{table}.{col}: {null_count} NULLs")
        cursor.close()
        return {'status': 'PASS' if not issues else 'FAIL', 'issues': issues}
    except psycopg2.Error as e:
        logger.error(f"✗ Error in completeness check: {str(e)}")
        return {'status': 'ERROR', 'issues': [str(e)]}
def check_uniqueness(conn, schema='staging'):
    """Check for duplicate values in key columns"""
    logger.info("Checking uniqueness...")
    issues = []
    try:
        cursor = conn.cursor()
        checks = {
            'customers': 'customer_id',
            'products': 'product_id',
            'transactions': 'transaction_id',
            'transaction_items': 'item_id'
        }
        for table, col in checks.items():
            cursor.execute(f"SELECT {col}, COUNT(*) as cnt FROM {schema}.{table} GROUP BY {col} HAVING COUNT(*) > 1;")
            duplicates = cursor.fetchall()
            if duplicates:
                for dup in duplicates:
                    issues.append(f"{schema}.{table}.{col}: {dup[1]} duplicates for ID {dup[0]}")
                    logger.warning(f"  ⚠ {schema}.{table}.{col}: {dup[1]} duplicates for {dup[0]}")
        cursor.close()
        return {'status': 'PASS' if not issues else 'FAIL', 'issues': issues}
    except psycopg2.Error as e:
        logger.error(f"✗ Error in uniqueness check: {str(e)}")
        return {'status': 'ERROR', 'issues': [str(e)]}
def check_validity(conn, schema='staging'):
    """Check for invalid data formats and ranges"""
    logger.info("Checking validity...")
    issues = []
    try:
        cursor = conn.cursor()
        # Check invalid emails
        cursor.execute(f"SELECT COUNT(*) FROM {schema}.customers WHERE email NOT LIKE '%@%';")
        invalid_emails = cursor.fetchone()[0]
        if invalid_emails > 0:
            issues.append(f"{schema}.customers: {invalid_emails} invalid email formats")
            logger.warning(f"  ⚠ {schema}.customers: {invalid_emails} invalid emails")
        # Check negative prices
        cursor.execute(f"SELECT COUNT(*) FROM {schema}.products WHERE price <= 0;")
        invalid_prices = cursor.fetchone()[0]
        if invalid_prices > 0:
            issues.append(f"{schema}.products: {invalid_prices} zero/negative prices")
            logger.warning(f"  ⚠ {schema}.products: {invalid_prices} invalid prices")
        # Check negative quantities
        cursor.execute(f"SELECT COUNT(*) FROM {schema}.transaction_items WHERE quantity <= 0;")
        invalid_qtys = cursor.fetchone()[0]
        if invalid_qtys > 0:
            issues.append(f"{schema}.transaction_items: {invalid_qtys} zero/negative quantities")
            logger.warning(f"  ⚠ {schema}.transaction_items: {invalid_qtys} invalid quantities")
        # Check negative transaction amounts
        cursor.execute(f"SELECT COUNT(*) FROM {schema}.transactions WHERE total_amount <= 0;")
        invalid_amounts = cursor.fetchone()[0]
        if invalid_amounts > 0:
            issues.append(f"{schema}.transactions: {invalid_amounts} zero/negative amounts")
            logger.warning(f"  ⚠ {schema}.transactions: {invalid_amounts} invalid amounts")
        cursor.close()
        return {'status': 'PASS' if not issues else 'FAIL', 'issues': issues}
    except psycopg2.Error as e:
        logger.error(f"✗ Error in validity check: {str(e)}")
        return {'status': 'ERROR', 'issues': [str(e)]}
def check_consistency(conn, schema='staging'):
    """Check for data consistency (e.g., line_total = quantity * unit_price)"""
    logger.info("Checking consistency...")
    issues = []
    try:
        cursor = conn.cursor()
        # Check line_total = quantity * unit_price
        cursor.execute(f"SELECT COUNT(*) FROM {schema}.transaction_items WHERE ABS(line_total - (quantity * unit_price)) > 0.01;")
        mismatch_count = cursor.fetchone()[0]
        if mismatch_count > 0:
            issues.append(f"{schema}.transaction_items: {mismatch_count} line_total mismatches")
            logger.warning(f"  ⚠ {schema}.transaction_items: {mismatch_count} consistency issues")
        cursor.close()
        return {'status': 'PASS' if not issues else 'FAIL', 'issues': issues}
    except psycopg2.Error as e:
        logger.error(f"✗ Error in consistency check: {str(e)}")
        return {'status': 'ERROR', 'issues': [str(e)]}
def check_referential_integrity(conn, schema='staging'):
    """Check for orphaned foreign key references"""
    logger.info("Checking referential integrity...")
    issues = []
    try:
        cursor = conn.cursor()
        # Check transactions with invalid customer_ids
        cursor.execute(f"""
            SELECT COUNT(*) FROM {schema}.transactions t 
            WHERE NOT EXISTS (SELECT 1 FROM {schema}.customers c WHERE c.customer_id = t.customer_id);
        """)
        orphan_customers = cursor.fetchone()[0]
        if orphan_customers > 0:
            issues.append(f"{schema}.transactions: {orphan_customers} orphaned customer references")
            logger.warning(f"  ⚠ {schema}.transactions: {orphan_customers} invalid customer IDs")
        # Check transaction_items with invalid product_ids
        cursor.execute(f"""
            SELECT COUNT(*) FROM {schema}.transaction_items ti 
            WHERE NOT EXISTS (SELECT 1 FROM {schema}.products p WHERE p.product_id = ti.product_id);
        """)
        orphan_products = cursor.fetchone()[0]
        if orphan_products > 0:
            issues.append(f"{schema}.transaction_items: {orphan_products} orphaned product references")
            logger.warning(f"  ⚠ {schema}.transaction_items: {orphan_products} invalid product IDs")
        # Check transaction_items with invalid transaction_ids
        cursor.execute(f"""
            SELECT COUNT(*) FROM {schema}.transaction_items ti 
            WHERE NOT EXISTS (SELECT 1 FROM {schema}.transactions t WHERE t.transaction_id = ti.transaction_id);
        """)
        orphan_transactions = cursor.fetchone()[0]
        if orphan_transactions > 0:
            issues.append(f"{schema}.transaction_items: {orphan_transactions} orphaned transaction references")
            logger.warning(f"  ⚠ {schema}.transaction_items: {orphan_transactions} invalid transaction IDs")
        cursor.close()
        return {'status': 'PASS' if not issues else 'FAIL', 'issues': issues}
    except psycopg2.Error as e:
        logger.error(f"✗ Error in referential integrity check: {str(e)}")
        return {'status': 'ERROR', 'issues': [str(e)]}
def calculate_quality_score(results, config):
    """Calculate overall data quality score"""
    weights = config['quality_checks']['weights']
    scores = {}
    for check_name, result in results.items():
        if result['status'] == 'PASS':
            scores[check_name] = 100.0
        elif result['status'] == 'FAIL':
            scores[check_name] = max(0, 100 - (len(result['issues']) * 5))
        else:
            scores[check_name] = 0.0
    overall_score = sum(scores.get(check, 0) * weight for check, weight in weights.items())
    return overall_score, scores
def create_quality_report(output_dir, results, overall_score, config):
    """Create quality report JSON"""
    report = {
        'quality_check_timestamp': datetime.now().isoformat(),
        'overall_quality_score': round(overall_score, 2),
        'threshold': config['quality_checks']['thresholds']['overall_score_min'],
        'status': 'PASS' if overall_score >= config['quality_checks']['thresholds']['overall_score_min'] else 'FAIL',
        'dimension_results': results,
        'recommendations': []
    }
    # Add recommendations
    for check_name, result in results.items():
        if result['status'] == 'FAIL':
            report['recommendations'].append(f"Review and fix {check_name} issues: {len(result['issues'])} problems found")
    output_file = os.path.join(output_dir, 'quality_report.json')
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"✓ Quality report saved to {output_file}")
    return report
def main():
    """Main execution"""
    print("\n" + "="*60)
    print("Data Quality Validation Pipeline")
    print("="*60 + "\n")
    try:
        # Load config
        config = load_config()
        logger.info("✓ Configuration loaded")
        # Get database connection
        conn = get_db_connection(config)
        # Run all quality checks
        results = {
            'completeness': check_completeness(conn),
            'uniqueness': check_uniqueness(conn),
            'validity': check_validity(conn),
            'consistency': check_consistency(conn),
            'referential_integrity': check_referential_integrity(conn)
        }
        # Calculate quality score
        overall_score, dimension_scores = calculate_quality_score(results, config)
        # Create report
        processed_dir = config['paths']['data_processed']
        Path(processed_dir).mkdir(parents=True, exist_ok=True)
        report = create_quality_report(processed_dir, results, overall_score, config)
        # Close connection
        conn.close()
        # Print summary
        print("\n" + "="*60)
        print("Quality Validation Complete")
        print("="*60)
        print(f"Overall Quality Score: {overall_score:.2f}%")
        print(f"Dimension Scores:")
        for dim, score in dimension_scores.items():
            print(f"  - {dim}: {score:.2f}%")
        print(f"Status: {report['status']}")
        print("="*60 + "\n")
        return report['status'] == 'PASS'
    except Exception as e:
        logger.error(f"✗ Quality validation pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
