"""
Celery application factory.

Configures the Celery instance, broker, result backend, and Beat schedule.
The periodic schedule is driven by the CRON_STR environment variable
(standard 5-field cron format: minute hour day_of_month month_of_year day_of_week).
"""

from celery import Celery
from celery.schedules import crontab

from src.config.settings import settings
from src.core.logger import Log


def _parse_cron_str(cron_str: str) -> dict:
    """
    Parse a standard 5-field cron string into kwargs for celery.schedules.crontab.

    Format: minute hour day_of_month month_of_year day_of_week
    Example: '0 9 * * *' → every day at 09:00

    Returns:
        dict suitable for unpacking into crontab(**kwargs).

    Raises:
        ValueError: If the cron string does not contain exactly 5 fields.
    """
    fields = cron_str.strip().split()
    if len(fields) != 5:
        raise ValueError(
            f"CRON_STR must have exactly 5 fields "
            f"(minute hour day_of_month month_of_year day_of_week), "
            f"got {len(fields)}: '{cron_str}'"
        )

    return {
        "minute": fields[0],
        "hour": fields[1],
        "day_of_month": fields[2],
        "month_of_year": fields[3],
        "day_of_week": fields[4],
    }


def create_celery_app() -> Celery:
    """
    Factory function that creates and configures a Celery application.

    - Broker: Redis (configured via REDIS_URL)
    - Result backend: Same Redis instance
    - Task discovery: src.tasks package
    - Beat schedule: Single periodic task parsed from CRON_STR
    """
    app = Celery("video_maker")

    # --- Broker & Backend ---
    app.conf.broker_url = settings.redis_url
    app.conf.result_backend = settings.redis_url

    # --- Serialization ---
    app.conf.task_serializer = "json"
    app.conf.result_serializer = "json"
    app.conf.accept_content = ["json"]

    # --- Reliability ---
    app.conf.task_acks_late = True
    app.conf.worker_prefetch_multiplier = 1
    app.conf.broker_connection_retry_on_startup = True

    # --- Timeouts ---
    # Video rendering + upload can take several minutes
    app.conf.task_time_limit = 600  # hard kill at 10 min
    app.conf.task_soft_time_limit = 540  # soft timeout at 9 min

    # --- Timezone ---
    app.conf.timezone = "Asia/Kolkata"
    app.conf.enable_utc = True

    # --- Task Discovery ---
    app.autodiscover_tasks(["src.tasks"])

    # --- Beat Schedule ---
    cron_kwargs = _parse_cron_str(settings.cron_str)
    Log.info(f"Celery Beat schedule configured: CRON_STR='{settings.cron_str}'")

    app.conf.beat_schedule = {
        "scheduled-reel-upload": {
            "task": "src.tasks.reel_upload.upload_reel",
            "schedule": crontab(**cron_kwargs),
            "options": {
                "queue": "default",
            },
        },
    }

    return app


# Module-level singleton used by Celery CLI and worker processes
celery_app = create_celery_app()
