from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from oracle.application.weekly_workflow import run_weekly_workflow, WorkflowResult


def _setup_logging(log_dir: Path) -> logging.Logger:
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"scheduler-{datetime.now().strftime('%Y%m%d')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )
    return logging.getLogger(__name__)


def _job_weekly_workflow(log_dir: Path) -> None:
    """Background job to run weekly workflow and log results"""
    logger = logging.getLogger(__name__)
    logger.info("Running weekly workflow...")

    result = run_weekly_workflow()

    # Log result to JSON file
    log_dir.mkdir(parents=True, exist_ok=True)
    result_file = log_dir / \
        f"workflow-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"

    result_data: dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "success": result.success,
        "details": result.details,
        "error": result.error,
        "ai_review_packet_path": str(result.ai_review_packet_path) if result.ai_review_packet_path else None,
        "weekly_report_path": str(result.weekly_report_path) if result.weekly_report_path else None,
        "promoted_config_path": str(result.promoted_config_path) if result.promoted_config_path else None,
        "governance_summary": result.governance_summary,
    }

    with open(result_file, "w") as f:
        json.dump(result_data, f, indent=2)

    logger.info(f"Workflow result logged to {result_file}")
    if result.success:
        logger.info(f"Weekly workflow completed successfully")
    else:
        logger.error(f"Weekly workflow failed: {result.error}")


def run_scheduler(
    cron_day_of_week: int = 0,
    cron_hour: int = 8,
    cron_minute: int = 0,
    log_dir: Path = Path("logs/weekly"),
) -> BackgroundScheduler:
    """
    Start background scheduler for weekly workflow.

    Args:
        cron_day_of_week: 0=Monday, 1=Tuesday, ..., 6=Sunday (default: Monday)
        cron_hour: Hour of day (0-23, default: 8)
        cron_minute: Minute of hour (0-59, default: 0)
        log_dir: Directory for job logs

    Returns:
        BackgroundScheduler instance (already running)
    """
    logger = _setup_logging(log_dir)

    scheduler = BackgroundScheduler()
    trigger = CronTrigger(
        day_of_week=cron_day_of_week,
        hour=cron_hour,
        minute=cron_minute,
    )
    scheduler.add_job(
        _job_weekly_workflow,
        trigger=trigger,
        args=[log_dir],
        id="weekly-workflow",
        name="Weekly AI Review and Governance Report",
        replace_existing=True,
    )

    scheduler.start()
    logger.info(
        f"Scheduler started. Weekly workflow scheduled for "
        f"day_of_week={cron_day_of_week} hour={cron_hour:02d} minute={cron_minute:02d}"
    )

    return scheduler


def main() -> int:
    parser = argparse.ArgumentParser(description="Weekly workflow scheduler")
    parser.add_argument(
        "--start",
        action="store_true",
        help="Start scheduler daemon",
    )
    parser.add_argument(
        "--day-of-week",
        type=int,
        default=0,
        help="Cron day of week (0=Monday, 6=Sunday, default: 0)",
    )
    parser.add_argument(
        "--hour",
        type=int,
        default=8,
        help="Cron hour (0-23, default: 8)",
    )
    parser.add_argument(
        "--minute",
        type=int,
        default=0,
        help="Cron minute (0-59, default: 0)",
    )
    parser.add_argument(
        "--log-dir",
        default="logs/weekly",
        help="Directory for job logs (default: logs/weekly)",
    )
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run workflow immediately (for testing)",
    )
    args = parser.parse_args()

    logger = _setup_logging(Path(args.log_dir))

    if args.run_now:
        logger.info("Running weekly workflow immediately (test mode)...")
        result = run_weekly_workflow()
        logger.info(f"Result: {result.success}")
        for detail in result.details:
            logger.info(f"  {detail}")
        return 0 if result.success else 1

    if args.start:
        logger.info("Starting scheduler...")
        scheduler = run_scheduler(
            cron_day_of_week=args.day_of_week,
            cron_hour=args.hour,
            cron_minute=args.minute,
            log_dir=Path(args.log_dir),
        )
        try:
            logger.info("Scheduler running. Press Ctrl+C to exit.")
            import time

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler stopped.")
            return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
