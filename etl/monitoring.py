import json
import os
import time
from datetime import datetime

REPORTS_DIR = "data/reports"
os.makedirs(REPORTS_DIR, exist_ok=True)


def write_pipeline_execution_report(status: str, details: dict):
    report = {
        "run_id": datetime.utcnow().isoformat(),
        "status": status,
        "details": details,
    }
    with open(os.path.join(REPORTS_DIR, "pipeline_execution_report.json"), "w") as f:
        json.dump(report, f, indent=2)


def write_monitoring_report(metrics: dict):
    report = {
        "generated_at": datetime.utcnow().isoformat(),
        "metrics": metrics,
    }
    with open(os.path.join(REPORTS_DIR, "monitoring_report.json"), "w") as f:
        json.dump(report, f, indent=2)
