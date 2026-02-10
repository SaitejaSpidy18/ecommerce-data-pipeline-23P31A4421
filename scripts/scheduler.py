# scripts/scheduler.py
import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import time
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
def load_config():
    """Load configuration from config/config.yaml"""
    config_path = "config/config.yaml"
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)
def run_pipeline():
    """Execute the main pipeline orchestration"""
    logger.info("="*60)
    logger.info("SCHEDULED PIPELINE EXECUTION STARTED")
    logger.info("="*60)
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, 'scripts/pipeline_orchestration.py'],
            capture_output=True,
            text=True,
            timeout=3600
        )
        if result.returncode == 0:
            logger.info("✓ Pipeline execution completed successfully")
            logger.info(result.stdout)
            return True
        else:
            logger.error(f"Pipeline execution failed: {result.stderr}")
            logger.error(result.stdout)
            return False
    except Exception as e:
        logger.error(f"✗ Error executing pipeline: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
def start_scheduler(config):
    """Start APScheduler with configured schedule"""
    if not config['scheduler']['enabled']:
        logger.info("Scheduler is disabled in config")
        return None
    scheduler = BackgroundScheduler()
    # Get scheduler configuration
    scheduler_type = config['scheduler'].get('type', 'cron')
    if scheduler_type == 'cron':
        cron_expression = config['scheduler'].get('cron_expression', '0 2 * * *')
        logger.info(f"Scheduling pipeline with cron expression: {cron_expression}")
        scheduler.add_job(
            run_pipeline,
            CronTrigger.from_crontab(cron_expression),
            id='pipeline_job',
            name='E-Commerce Data Pipeline',
            replace_existing=True,
            misfire_grace_time=60
        )
    elif scheduler_type == 'daily':
        daily_run_time = config['scheduler'].get('daily_run_time', '02:00')
        hour, minute = map(int, daily_run_time.split(':'))
        logger.info(f"Scheduling pipeline to run daily at {daily_run_time}")
        scheduler.add_job(
            run_pipeline,
            'cron',
            hour=hour,
            minute=minute,
            id='pipeline_job',
            name='E-Commerce Data Pipeline',
            replace_existing=True,
            misfire_grace_time=60
        )
    else:
        logger.warning(f"Unknown scheduler type: {scheduler_type}")
        return None
    # Start scheduler
    try:
        scheduler.start()
        logger.info("✓ Scheduler started successfully")
        logger.info(f"Next scheduled run: {scheduler.get_job('pipeline_job').next_run_time}")
        return scheduler
    except Exception as e:
        logger.error(f"✗ Failed to start scheduler: {str(e)}")
        return None
def main():
    """Main scheduler function"""
    print("\n" + "="*60)
    print("E-COMMERCE DATA PIPELINE SCHEDULER")
    print("="*60 + "\n")
    try:
        # Load configuration
        config = load_config()
        logger.info("✓ Configuration loaded successfully")
        # Create log directory
        log_dir = config['paths'].get('logs', 'logs')
        Path(log_dir).mkdir(parents=True, exist_ok=True)
        logger.info("✓ Log directory ready")
        # Start scheduler
        scheduler = start_scheduler(config)
        if scheduler is None:
            logger.warning("Scheduler not started - check configuration")
            return False
        # Keep scheduler running
        logger.info("Scheduler is running. Press Ctrl+C to stop.")
        print("="*60)
        print("Scheduler is running. Press Ctrl+C to stop.")
        print("="*60 + "\n")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Scheduler shutdown requested")
            scheduler.shutdown()
            print("\nScheduler stopped.")
            return True
    except Exception as e:
        logger.error(f"✗ Scheduler error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
