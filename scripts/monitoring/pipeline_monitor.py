# scripts/monitoring/pipeline_monitor.py
import os
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import yaml
import psycopg2
from psycopg2.extras import RealDictCursor
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monitoring.log'),
        logging.StreamHandler()
    ]
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
        return conn
    except psycopg2.Error as e:
        logger.error(f"✗ Failed to connect to database: {str(e)}")
        raise
def check_staging_health(conn):
    """Check staging schema health metrics"""
    logger.info("Checking staging schema health...")
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        health = {
            'schema': 'staging',
            'timestamp': datetime.now().isoformat(),
            'tables': {}
        }
        tables = ['customers', 'products', 'transactions', 'transaction_items']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as row_count FROM staging.{table};")
            result = cursor.fetchone()
            row_count = result['row_count'] if result else 0
            health['tables'][table] = {
                'row_count': row_count,
                'status': 'OK' if row_count > 0 else 'EMPTY'
            }
        cursor.close()
        logger.info(f"✓ Staging schema health checked")
        return health
    except Exception as e:
        logger.error(f"✗ Error checking staging health: {str(e)}")
        return None
def check_production_health(conn):
    """Check production schema health metrics"""
    logger.info("Checking production schema health...")
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        health = {
            'schema': 'production',
            'timestamp': datetime.now().isoformat(),
            'tables': {}
        }
        tables = ['customers', 'products', 'transactions', 'transaction_items']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) as row_count FROM production.{table};")
            result = cursor.fetchone()
            row_count = result['row_count'] if result else 0
            health['tables'][table] = {
                'row_count': row_count,
                'status': 'OK' if row_count > 0 else 'EMPTY'
            }
        cursor.close()
        logger.info(f"✓ Production schema health checked")
        return health
    except Exception as e:
        logger.error(f"✗ Error checking production health: {str(e)}")
        return None
def check_warehouse_health(conn):
    """Check warehouse schema health metrics"""
    logger.info("Checking warehouse schema health...")
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        health = {
            'schema': 'warehouse',
            'timestamp': datetime.now().isoformat(),
            'dimensions': {},
            'facts': {}
        }
        # Check dimensions
        dimensions = ['dim_customers', 'dim_products', 'dim_date', 'dim_payment_method', 'dim_transaction_status']
        for dim in dimensions:
            cursor.execute(f"SELECT COUNT(*) as row_count FROM warehouse.{dim};")
            result = cursor.fetchone()
            row_count = result['row_count'] if result else 0
            health['dimensions'][dim] = {
                'row_count': row_count,
                'status': 'OK' if row_count > 0 else 'EMPTY'
            }
        # Check facts
        cursor.execute("SELECT COUNT(*) as row_count FROM warehouse.fact_sales;")
        result = cursor.fetchone()
        fact_count = result['row_count'] if result else 0
        health['facts']['fact_sales'] = {
            'row_count': fact_count,
            'status': 'OK' if fact_count > 0 else 'EMPTY'
        }
        # Check aggregates
        cursor.execute("SELECT COUNT(*) as row_count FROM warehouse.agg_daily_sales;")
        result = cursor.fetchone()
        agg_count = result['row_count'] if result else 0
        health['facts']['agg_daily_sales'] = {
            'row_count': agg_count,
            'status': 'OK' if agg_count > 0 else 'EMPTY'
        }
        cursor.close()
        logger.info(f"✓ Warehouse schema health checked")
        return health
    except Exception as e:
        logger.error(f"✗ Error checking warehouse health: {str(e)}")
        return None
def check_data_quality_metrics(conn):
    """Check current data quality metrics"""
    logger.info("Checking data quality metrics...")
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'quality_checks': {}
        }
        # Check NULL values in critical columns
        cursor.execute("""
            SELECT COUNT(*) as null_count FROM production.customers 
            WHERE email IS NULL OR first_name IS NULL OR last_name IS NULL;
        """)
        result = cursor.fetchone()
        null_count = result['null_count'] if result else 0
        metrics['quality_checks']['null_values'] = {
            'count': null_count,
            'status': 'OK' if null_count == 0 else 'WARNING'
        }
        # Check duplicate IDs
        cursor.execute("""
            SELECT COUNT(*) as dup_count FROM (
                SELECT customer_id, COUNT(*) FROM production.customers 
                GROUP BY customer_id HAVING COUNT(*) > 1
            ) t;
        """)
        result = cursor.fetchone()
        dup_count = result['dup_count'] if result else 0
        metrics['quality_checks']['duplicates'] = {
            'count': dup_count,
            'status': 'OK' if dup_count == 0 else 'WARNING'
        }
        # Check referential integrity
        cursor.execute("""
            SELECT COUNT(*) as orphan_count FROM production.transactions t
            WHERE NOT EXISTS (SELECT 1 FROM production.customers c WHERE c.customer_id = t.customer_id);
        """)
        result = cursor.fetchone()
        orphan_count = result['orphan_count'] if result else 0
        metrics['quality_checks']['referential_integrity'] = {
            'orphaned_records': orphan_count,
            'status': 'OK' if orphan_count == 0 else 'ERROR'
        }
        # Check invalid data ranges
        cursor.execute("""
            SELECT COUNT(*) as invalid_count FROM production.products 
            WHERE price <= 0 OR cost <= 0 OR price < cost;
        """)
        result = cursor.fetchone()
        invalid_count = result['invalid_count'] if result else 0
        metrics['quality_checks']['invalid_ranges'] = {
            'count': invalid_count,
            'status': 'OK' if invalid_count == 0 else 'WARNING'
        }
        cursor.close()
        logger.info(f"✓ Data quality metrics checked")
        return metrics
    except Exception as e:
        logger.error(f"✗ Error checking quality metrics: {str(e)}")
        return None
def check_pipeline_logs():
    """Check recent pipeline execution logs"""
    logger.info("Checking pipeline logs...")
    try:
        log_files = {
            'pipeline_execution_report': 'data/processed/pipeline_execution_report.json',
            'monitoring_report': 'data/processed/monitoring_report.json',
            'quality_report': 'data/processed/quality_report.json',
            'transformation_summary': 'data/processed/transformation_summary.json'
        }
        logs = {
            'timestamp': datetime.now().isoformat(),
            'reports': {}
        }
        for name, file_path in log_files.items():
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        content = json.load(f)
                        file_stat = os.stat(file_path)
                        logs['reports'][name] = {
                            'exists': True,
                            'last_updated': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                            'status': content.get('status', 'UNKNOWN')
                        }
                except Exception as e:
                    logs['reports'][name] = {
                        'exists': True,
                        'error': str(e)
                    }
            else:
                logs['reports'][name] = {
                    'exists': False,
                    'status': 'MISSING'
                }
        logger.info(f"✓ Pipeline logs checked")
        return logs
    except Exception as e:
        logger.error(f"✗ Error checking pipeline logs: {str(e)}")
        return None
def create_monitoring_report(output_dir, staging_health, production_health, warehouse_health, quality_metrics, pipeline_logs):
    """Create comprehensive monitoring report"""
    report = {
        'monitoring_timestamp': datetime.now().isoformat(),
        'summary': {
            'overall_status': 'HEALTHY' if all([
                staging_health,
                production_health,
                warehouse_health,
                quality_metrics,
                pipeline_logs
            ]) else 'DEGRADED'
        },
        'schemas': {
            'staging': staging_health,
            'production': production_health,
            'warehouse': warehouse_health
        },
        'data_quality': quality_metrics,
        'pipeline_logs': pipeline_logs
    }
    output_file = os.path.join(output_dir, 'system_monitoring_report.json')
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"✓ Monitoring report saved to {output_file}")
    return report
def print_monitoring_summary(report):
    """Print monitoring summary to console"""
    print("\n" + "="*60)
    print("PIPELINE MONITORING REPORT")
    print("="*60)
    print(f"Timestamp: {report['monitoring_timestamp']}")
    print(f"Overall Status: {report['summary']['overall_status']}")
    print("\nSchema Health:")
    for schema_name, schema_data in report['schemas'].items():
        if schema_data:
            print(f"\n  {schema_name.upper()}:")
            if 'tables' in schema_data:
                for table, info in schema_data['tables'].items():
                    print(f"    - {table}: {info['row_count']} rows ({info['status']})")
            elif 'dimensions' in schema_data:
                print(f"    Dimensions: {len(schema_data['dimensions'])} total")
                print(f"    Facts: {len(schema_data['facts'])} total")
    print("\nData Quality:")
    if report['data_quality'] and 'quality_checks' in report['data_quality']:
        for check, result in report['data_quality']['quality_checks'].items():
            status = result.get('status', 'UNKNOWN')
            print(f"  - {check}: {status}")
    print("\nPipeline Reports:")
    if report['pipeline_logs'] and 'reports' in report['pipeline_logs']:
        for report_name, info in report['pipeline_logs']['reports'].items():
            status = 'OK' if info.get('exists') else 'MISSING'
            print(f"  - {report_name}: {status}")
    print("="*60 + "\n")
def main():
    """Main monitoring function"""
    print("\n" + "="*60)
    print("E-COMMERCE DATA PIPELINE MONITOR")
    print("="*60 + "\n")
    try:
        # Load configuration
        config = load_config()
        logger.info("✓ Configuration loaded successfully")
        # Create output directory
        output_dir = config['paths']['data_processed']
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        # Get database connection
        conn = get_db_connection(config)
        # Collect monitoring data
        staging_health = check_staging_health(conn)
        production_health = check_production_health(conn)
        warehouse_health = check_warehouse_health(conn)
        quality_metrics = check_data_quality_metrics(conn)
        pipeline_logs = check_pipeline_logs()
        # Create report
        report = create_monitoring_report(
            output_dir,
            staging_health,
            production_health,
            warehouse_health,
            quality_metrics,
            pipeline_logs
        )
        # Print summary
        print_monitoring_summary(report)
        # Close connection
        conn.close()
        logger.info("✓ Monitoring completed successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Monitoring failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
