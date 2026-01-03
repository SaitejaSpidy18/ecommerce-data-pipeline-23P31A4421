import os
import sys
import json
import logging
from datetime import datetime
import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

LOG_DIR = Path(PROJECT_ROOT) / "logs"
LOG_DIR.mkdir(exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_file = LOG_DIR / f"pipeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
file_handler = logging.FileHandler(log_file)
console_handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
logger.addHandler(file_handler)
logger.addHandler(console_handler)


class PipelineOrchestrator:
    def __init__(self):
        self.start_time = datetime.now()
    
    def get_db_connection(self):
        db_path = PROJECT_ROOT / "data" / "ecommerce.db"
        return sqlite3.connect(str(db_path))
    
    def phase_1_data_generation(self):
        logger.info("=" * 80)
        logger.info("PHASE 1: DATA GENERATION")
        logger.info("=" * 80)
        try:
            from scripts.data_generation.generate_data import (
                generate_customers, generate_products, generate_transactions,
                generate_transaction_items, validate_referential_integrity
            )
            import yaml
            
            config_path = PROJECT_ROOT / "config" / "config.yaml"
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            num_customers = config['data_generation']['num_customers']
            num_products = config['data_generation']['num_products']
            num_transactions = config['data_generation']['num_transactions']
            
            logger.info(f"Generating {num_customers} customers...")
            customers_df = generate_customers(num_customers)
            logger.info(f"✓ Generated {len(customers_df)} customers")
            
            logger.info(f"Generating {num_products} products...")
            products_df = generate_products(num_products)
            logger.info(f"✓ Generated {len(products_df)} products")
            
            logger.info(f"Generating {num_transactions} transactions...")
            transactions_df = generate_transactions(num_transactions, customers_df)
            logger.info(f"✓ Generated {len(transactions_df)} transactions")
            
            logger.info("Generating transaction items...")
            items_df = generate_transaction_items(transactions_df, products_df)
            logger.info(f"✓ Generated {len(items_df)} items")
            
            logger.info("Validating referential integrity...")
            integrity_result = validate_referential_integrity(customers_df, products_df, transactions_df, items_df)
            logger.info("✓ Referential integrity passed")
            
            data_dir = PROJECT_ROOT / "data" / "raw"
            data_dir.mkdir(parents=True, exist_ok=True)
            customers_df.to_csv(data_dir / "customers.csv", index=False)
            products_df.to_csv(data_dir / "products.csv", index=False)
            transactions_df.to_csv(data_dir / "transactions.csv", index=False)
            items_df.to_csv(data_dir / "transaction_items.csv", index=False)
            logger.info("✓ Data saved to CSV")
            logger.info(f"✓ Phase 1 completed\n")
        except Exception as e:
            logger.error(f"✗ Phase 1 FAILED: {str(e)}")
            raise
    
    def phase_2_data_ingestion(self):
        logger.info("=" * 80)
        logger.info("PHASE 2: DATA INGESTION")
        logger.info("=" * 80)
        try:
            conn = self.get_db_connection()
            data_dir = PROJECT_ROOT / "data" / "raw"
            
            tables = [
                ("customers.csv", "staging_customers"),
                ("products.csv", "staging_products"),
                ("transactions.csv", "staging_transactions"),
                ("transaction_items.csv", "staging_transaction_items")
            ]
            
            for csv_file, table_name in tables:
                csv_path = data_dir / csv_file
                logger.info(f"Loading {csv_file}...")
                df = pd.read_csv(csv_path)
                df.to_sql(table_name, conn, if_exists='replace', index=False)
                logger.info(f"✓ Loaded {len(df)} records to {table_name}")
            
            conn.commit()
            conn.close()
            logger.info(f"✓ Phase 2 completed\n")
        except Exception as e:
            logger.error(f"✗ Phase 2 FAILED: {str(e)}")
            raise
    
    def phase_3_data_quality(self):
        logger.info("=" * 80)
        logger.info("PHASE 3: DATA QUALITY CHECKS")
        logger.info("=" * 80)
        try:
            from scripts.quality_checks.validate_data import (
                check_null_values, check_duplicates, check_data_ranges, calculate_quality_score
            )
            
            conn = self.get_db_connection()
            logger.info("Running quality checks...")
            null_check = check_null_values(conn, "staging")
            dup_check = check_duplicates(conn, "staging")
            range_check = check_data_ranges(conn, "staging")
            
            check_results = {"null_values": null_check, "duplicates": dup_check, "data_ranges": range_check}
            quality_score = calculate_quality_score(check_results)
            logger.info(f"✓ Quality Score: {quality_score:.2f}%")
            conn.close()
            logger.info(f"✓ Phase 3 completed\n")
        except Exception as e:
            logger.error(f"✗ Phase 3 FAILED: {str(e)}")
            raise
    
    def phase_4_transformation(self):
        logger.info("=" * 80)
        logger.info("PHASE 4: DATA TRANSFORMATION")
        logger.info("=" * 80)
        try:
            conn = self.get_db_connection()
            logger.info("Reading staging data...")
            staging_customers = pd.read_sql("SELECT * FROM staging_customers", conn)
            staging_products = pd.read_sql("SELECT * FROM staging_products", conn)
            staging_transactions = pd.read_sql("SELECT * FROM staging_transactions", conn)
            staging_items = pd.read_sql("SELECT * FROM staging_transaction_items", conn)
            
            logger.info(f"✓ Read {len(staging_customers)} customers")
            logger.info(f"✓ Read {len(staging_products)} products")
            logger.info(f"✓ Read {len(staging_transactions)} transactions")
            logger.info(f"✓ Read {len(staging_items)} items")
            
            logger.info("Creating production tables...")
            staging_customers.to_sql("production_customers", conn, if_exists='replace', index=False)
            staging_products.to_sql("production_products", conn, if_exists='replace', index=False)
            staging_transactions.to_sql("production_transactions", conn, if_exists='replace', index=False)
            staging_items.to_sql("production_transaction_items", conn, if_exists='replace', index=False)
            
            conn.commit()
            conn.close()
            logger.info(f"✓ Phase 4 completed\n")
        except Exception as e:
            logger.error(f"✗ Phase 4 FAILED: {str(e)}")
            raise
    
    def phase_5_warehouse_loading(self):
        logger.info("=" * 80)
        logger.info("PHASE 5: WAREHOUSE LOADING")
        logger.info("=" * 80)
        try:
            conn = self.get_db_connection()
            logger.info("Reading production data...")
            prod_customers = pd.read_sql("SELECT * FROM production_customers", conn)
            prod_products = pd.read_sql("SELECT * FROM production_products", conn)
            prod_items = pd.read_sql("SELECT * FROM production_transaction_items", conn)
            
            logger.info("Building warehouse dimension tables...")
            prod_customers.to_sql("warehouse_dim_customers", conn, if_exists='replace', index=False)
            logger.info("✓ Built dim_customers")
            
            prod_products.to_sql("warehouse_dim_products", conn, if_exists='replace', index=False)
            logger.info("✓ Built dim_products")
            
            date_range = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
            dim_date = pd.DataFrame({
                'date_key': range(len(date_range)),
                'full_date': date_range,
                'year': date_range.year,
                'month': date_range.month,
                'day': date_range.day,
                'quarter': date_range.quarter,
                'week': date_range.isocalendar().week
            })
            dim_date.to_sql("warehouse_dim_date", conn, if_exists='replace', index=False)
            logger.info("✓ Built dim_date")
            
            payment_methods = pd.DataFrame({
                'payment_method_id': range(1, 6),
                'payment_method_name': ['Credit Card', 'Debit Card', 'UPI', 'COD', 'Net Banking']
            })
            payment_methods.to_sql("warehouse_dim_payment_method", conn, if_exists='replace', index=False)
            logger.info("✓ Built dim_payment_method")
            
            prod_items.to_sql("warehouse_fact_sales", conn, if_exists='replace', index=False)
            logger.info("✓ Built fact_sales")
            
            conn.commit()
            conn.close()
            logger.info(f"✓ Phase 5 completed\n")
        except Exception as e:
            logger.error(f"✗ Phase 5 FAILED: {str(e)}")
            raise
    
    def run(self):
        logger.info("\n" + "="*80)
        logger.info("PIPELINE ORCHESTRATION STARTED")
        logger.info("="*80 + "\n")
        
        try:
            self.phase_1_data_generation()
            self.phase_2_data_ingestion()
            self.phase_3_data_quality()
            self.phase_4_transformation()
            self.phase_5_warehouse_loading()
            
            logger.info("="*80)
            logger.info("✓ ALL PHASES COMPLETED SUCCESSFULLY")
            logger.info("="*80)
            return True
        except Exception as e:
            logger.error("="*80)
            logger.error("✗ PIPELINE FAILED")
            logger.error("="*80)
            return False
    def save_execution_report(self):
        """Save execution report to JSON"""
        report_dir = PROJECT_ROOT / "data" / "processed"
        report_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = report_dir / f"pipeline_execution_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(self.execution_report, f, indent=2)
        
        logger.info(f"\n✓ Execution report saved to: {report_file}")
        return report_file


if __name__ == "__main__":
    orchestrator = PipelineOrchestrator()
    success = orchestrator.run()
    sys.exit(0 if success else 1)
