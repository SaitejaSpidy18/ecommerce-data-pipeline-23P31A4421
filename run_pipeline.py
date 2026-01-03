import time

from etl.ingest import run_ingestion
from etl.transform import run_transformations
from etl.quality_checks import run_quality_checks
from etl.monitoring import write_pipeline_execution_report, write_monitoring_report


def main():
    overall_metrics = {}
    start = time.time()
    status = "success"

    try:
        ingestion_report = run_ingestion()
        overall_metrics["ingestion"] = ingestion_report

        transform_report = run_transformations()
        overall_metrics["transformations"] = transform_report

        quality_report = run_quality_checks()
        overall_metrics["quality"] = quality_report

    except Exception as e:
        status = "failed"
        overall_metrics["error"] = str(e)

    end = time.time()
    overall_metrics["total_duration_seconds"] = end - start

    write_pipeline_execution_report(status=status, details=overall_metrics)
    write_monitoring_report(metrics=overall_metrics)


if __name__ == "__main__":
    main()
