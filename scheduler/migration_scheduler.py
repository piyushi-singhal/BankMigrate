import time
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from migration_engine.pipeline import run_pipeline

class MigrationScheduler:
    """
    Automated Migration Job Scheduler using APScheduler.
    Executes recurring migration runs on a cron or interval schedule.
    """
    def __init__(self, interval_minutes: int = 5):
        self.interval_minutes = interval_minutes
        self.scheduler = BackgroundScheduler()

    def _scheduled_job(self):
        timestamp_str = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        run_id = f"SCHED-RUN-{timestamp_str}"
        print(f"\n[SCHEDULER TRIGGER] Auto-triggering scheduled migration run '{run_id}' at {datetime.datetime.now()}...")
        try:
            result = run_pipeline(run_id=run_id, clear_target=False)
            print(f"[SCHEDULER SUCCESS] Run '{run_id}' finished with status: {result['status']}")
        except Exception as e:
            print(f"[SCHEDULER ERROR] Scheduled run '{run_id}' failed: {e}")

    def start(self):
        """Starts the background scheduler."""
        print(f"Starting BankMigrate Automated Scheduler (Interval: every {self.interval_minutes} minutes)...")
        self.scheduler.add_job(
            func=self._scheduled_job,
            trigger=IntervalTrigger(minutes=self.interval_minutes),
            id="bankmigrate_auto_run",
            name="BankMigrate Recurring Batch Migration",
            replace_existing=True
        )
        self.scheduler.start()
        print("Scheduler is active and running in background.")

    def stop(self):
        """Stops the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("Scheduler stopped.")

    def run_one_shot(self):
        """Executes a single scheduled job run immediately for verification."""
        print("[SCHEDULER TEST] Triggering immediate test execution of scheduled job...")
        self._scheduled_job()
