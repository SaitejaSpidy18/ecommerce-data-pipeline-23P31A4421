# scripts/pipeline_orchestration.py
import os
import sys
import json
import logging
from datetime import datetime
from pathlib import Path
import yaml
import traceback
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
def load_config():
    """Load configuration from config/config.yaml"""
    config_path = "config/config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
def create_log_directory(config):
    """Create logs directory"""
    log_dir = config['paths'].get('logs', 'logs')
    Path(log_dir).mkdir(parents=True, exist_ok=True)
def run_data_generation(config):
    """Execute data generation script"""
    logger.info("="*60)
    logger.info("PHASE 1: DATA GENERATION")
    logger.info("="*60)
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, 'scripts/data_generation/generate_data.py'],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            logger.error(f"Data generation failed: {result.stderr}")
            return False
        logger.info("✓ Data generation completed successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Data generation error: {str(e)}")
        traceback.print_exc()
        return False
def run_ingestion(config):
    """Execute data ingestion script"""
    logger.info("="*60)
    logger.info("PHASE 2: DATA INGESTION")
    logger.info("="*60)
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, 'scripts/ingestion/ingest_to_staging.py'],
            capture_output=True,
            text=True,
            timeout=600
        )
        if result.returncode != 0:
            logger.error(f"Data ingestion failed: {result.stderr}")
            return False
        logger.info("✓ Data ingestion completed successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Data ingestion error: {str(e)}")
        traceback.print_exc()
        return False
def run_quality_checks(config):
    """Execute data quality checks"""
    logger.info("="*60)
    logger.info("PHASE 3: QUALITY CHECKS")
    logger.info("="*60)
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, 'scripts/quality_checks/validate_data.py'],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            logger.warning(f"Quality checks reported issues: {result.stderr}")
        logger.info("✓ Quality checks completed")
        return True
    except Exception as e:
        logger.error(f"✗ Quality checks error: {str(e)}")
        traceback.print_exc()
        return False
def run_transformation(config):
    """Execute staging to production transformation"""
    logger.info("="*60)
    logger.info("PHASE 4: STAGING TO PRODUCTION TRANSFORMATION")
    logger.info("="*60)
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, 'scripts/transformation/staging_to_production.py'],
            capture_output=True,
            text=True,
            timeout=600
        )
        if result.returncode != 0:
            logger.error(f"Transformation failed: {result.stderr}")
            return False
        logger.info("✓ Staging to production transformation completed successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Transformation error: {str(e)}")
        traceback.print_exc()
        return False
def run_warehouse_load(config):
    """Execute warehouse loading"""
    logger.info("="*60)
    logger.info("PHASE 5: WAREHOUSE LOAD")
    logger.info("="*60)
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, 'scripts/transformation/load_warehouse.py'],
            capture_output=True,
            text=True,
            timeout=600
        )
        if result.returncode != 0:
            logger.error(f"Warehouse load failed: {result.stderr}")
            return False
        logger.info("✓ Warehouse load completed successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Warehouse load error: {str(e)}")
        traceback.print_exc()
        return False
def run_analytics_queries(config):
    """Execute analytical queries and export results"""
    logger.info("="*60)
    logger.info("PHASE 6: ANALYTICS & REPORTING")
    logger.info("="*60)
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, 'scripts/analytics/run_analytics.py'],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            logger.warning(f"Analytics execution had issues: {result.stderr}")
        logger.info("✓ Analytics queries executed")
        return True
    except Exception as e:
        logger.error(f"✗ Analytics error: {str(e)}")
        traceback.print_exc()
        return False
def create_pipeline_execution_report(output_dir, pipeline_results, duration_seconds):
    """Create pipeline execution report"""
    report = {
        'pipeline_execution_timestamp': datetime.now().isoformat(),
        'total_duration_seconds': duration_seconds,
        'phases': {
            'data_generation': {
                'status': 'SUCCESS' if pipeline_results['data_generation'] else 'FAILED',
                'completed': pipeline_results['data_generation']
            },
            'data_ingestion': {
                'status': 'SUCCESS' if pipeline_results['ingestion'] else 'FAILED',
                'completed': pipeline_results['ingestion']
            },
            'quality_checks': {
                'status': 'SUCCESS' if pipeline_results['quality_checks'] else 'FAILED',
                'completed': pipeline_results['quality_checks']
            },
            'transformation': {
                'status': 'SUCCESS' if pipeline_results['transformation'] else 'FAILED',
                'completed': pipeline_results['transformation']
            },
            'warehouse_load': {
                'status': 'SUCCESS' if pipeline_results['warehouse_load'] else 'FAILED',
                'completed': pipeline_results['warehouse_load']
            },
            'analytics': {
                'status': 'SUCCESS' if pipeline_results['analytics'] else 'FAILED',
                'completed': pipeline_results['analytics']
            }
        },
        'overall_status': 'SUCCESS' if all(pipeline_results.values()) else 'PARTIAL_FAILURE',
        'timestamp': datetime.now().isoformat()
    }
    output_file = os.path.join(output_dir, 'pipeline_execution_report.json')
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"✓ Pipeline execution report saved to {output_file}")
    return report
def create_monitoring_report(output_dir, duration_seconds):
    """Create monitoring report with performance metrics"""
    report = {
        'monitoring_timestamp': datetime.now().isoformat(),
        'pipeline_duration_seconds': duration_seconds,
        'pipeline_duration_minutes': round(duration_seconds / 60, 2),
        'start_time': (datetime.now().timestamp() - duration_seconds),
        'end_time': datetime.now().timestamp(),
        'status': 'COMPLETED',
        'performance_notes': [
            f'Total pipeline execution time: {round(duration_seconds / 60, 2)} minutes',
            'All critical phases executed',
            'Check logs/pipeline.log for detailed execution logs'
        ]
    }
    output_file = os.path.join(output_dir, 'monitoring_report.json')
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    logger.info(f"✓ Monitoring report saved to {output_file}")
    return report
def main():
    """Main orchestration function"""
    print("\n" + "="*60)
    print("E-COMMERCE DATA PIPELINE ORCHESTRATOR")
    print("="*60 + "\n")
    pipeline_start_time = datetime.now()
    try:
        # Load configuration
        config = load_config()
        logger.info("✓ Configuration loaded successfully")
        # Create log directory
        create_log_directory(config)
        logger.info("✓ Log directory ready")
        # Initialize pipeline results tracking
        pipeline_results = {
            'data_generation': False,
            'ingestion': False,
            'quality_checks': False,
            'transformation': False,
            'warehouse_load': False,
            'analytics': False
        }
        # PHASE 1: Data Generation
        pipeline_results['data_generation'] = run_data_generation(config)
        if not pipeline_results['data_generation']:
            raise Exception("Data generation failed - aborting pipeline")
        # PHASE 2: Data Ingestion
        pipeline_results['ingestion'] = run_ingestion(config)
        if not pipeline_results['ingestion']:
            raise Exception("Data ingestion failed - aborting pipeline")
        # PHASE 3: Quality Checks
        pipeline_results['quality_checks'] = run_quality_checks(config)
        # PHASE 4: Transformation
        pipeline_results['transformation'] = run_transformation(config)
        if not pipeline_results['transformation']:
            raise Exception("Transformation failed - aborting pipeline")
        # PHASE 5: Warehouse Load
        pipeline_results['warehouse_load'] = run_warehouse_load(config)
        if not pipeline_results['warehouse_load']:
            raise Exception("Warehouse load failed - aborting pipeline")
        # PHASE 6: Analytics & Reporting
        pipeline_results['analytics'] = run_analytics_queries(config)
        # Create reports
        duration = (datetime.now() - pipeline_start_time).total_seconds()
        processed_dir = config['paths']['data_processed']
        Path(processed_dir).mkdir(parents=True, exist_ok=True)
        execution_report = create_pipeline_execution_report(processed_dir, pipeline_results, duration)
        monitoring_report = create_monitoring_report(processed_dir, duration)
        # Final summary
        print("\n" + "="*60)
        print("PIPELINE EXECUTION SUMMARY")
        print("="*60)
        print(f"Overall Status: {execution_report['overall_status']}")
        print(f"Total Duration: {round(duration / 60, 2)} minutes")
        print("\nPhase Results:")
        for phase, result in pipeline_results.items():
            status = "✓ SUCCESS" if result else "✗ FAILED"
            print(f"  {phase}: {status}")
        print("="*60 + "\n")
        return all(pipeline_results.values())
    except Exception as e:
        logger.error(f"✗ Pipeline execution failed: {str(e)}")
        traceback.print_exc()
        print("\n" + "="*60)
        print("PIPELINE FAILED")
        print("="*60)
        print(f"Error: {str(e)}")
        print("Check logs/pipeline.log for details")
        print("="*60 + "\n")
        return False
if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
