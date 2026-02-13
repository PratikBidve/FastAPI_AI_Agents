"""
Celery tasks for Job Copilot agent system.
Enables asynchronous job processing with Redis backend.

Setup:
1. Add to requirements: celery[redis]
2. Configure in settings
3. Start worker: celery -A app.services.agents.celery_tasks worker -l info
4. Start beat (if needed): celery -A app.services.agents.celery_tasks beat
"""

import asyncio
import logging

from celery import Celery, Task  # type: ignore[import-untyped]
from celery.exceptions import SoftTimeLimitExceeded  # type: ignore[import-untyped]

from app.services.agents import get_job_copilot_graph, init_llm
from app.services.agents.utils import export_workflow_result, get_summary

logger = logging.getLogger(__name__)

# Initialize Celery app
# This should be configured in your project settings
app = Celery(
    'job_copilot',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
)

# Configuration
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_soft_time_limit=60,  # 60 second soft timeout
    task_time_limit=120,       # 120 second hard timeout
    result_expires=3600,       # Results expire in 1 hour
    worker_prefetch_multiplier=1,  # Don't prefetch tasks
)


class CallbackTask(Task):
    """Task with callback support for success/failure handlers."""

    def on_success(self, retval: object, task_id: str, args: tuple, kwargs: dict) -> None:
        """Success callback."""
        logger.info(f"Task {task_id} completed successfully")

    def on_retry(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: object) -> None:
        """Retry callback."""
        logger.warning(f"Task {task_id} retrying due to: {exc}")

    def on_failure(self, exc: Exception, task_id: str, args: tuple, kwargs: dict, einfo: object) -> None:
        """Failure callback."""
        logger.error(f"Task {task_id} failed with exception: {exc}", exc_info=einfo)


app.Task = CallbackTask


@app.task(
    name='job_copilot.analyze_application',
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def analyze_application_task(
    self,
    job_description: str,
    resume: str,
    user_id: str | None = None,
) -> dict[str, object]:
    """
    Analyze a job application asynchronously.

    Args:
        job_description: Job posting text
        resume: Resume text
        user_id: Optional user identifier for tracking

    Returns:
        Dictionary with analysis results

    Raises:
        Exception: Re-raised after max retries exceeded
    """
    task_id = self.request.id

    try:
        logger.info(f"Starting task {task_id} for user {user_id}")

        # Initialize LLM
        init_llm()

        # Get graph
        graph = get_job_copilot_graph()

        # Run workflow (need to handle async in sync task)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Already in async context
            import nest_asyncio  # type: ignore[import-untyped]
            nest_asyncio.apply()

        result = loop.run_until_complete(
            graph.execute(job_description=job_description, resume=resume)
        )

        # Export results
        exported = export_workflow_result(result)
        exported["task_id"] = task_id
        exported["user_id"] = user_id
        exported["summary"] = get_summary(result)

        logger.info(f"Task {task_id} completed with score: {result.get('matching_score'):.1%}")

        return exported

    except SoftTimeLimitExceeded:
        logger.warning(f"Task {task_id} hit soft time limit")
        raise self.retry(exc=SoftTimeLimitExceeded(), countdown=30)

    except Exception as exc:
        logger.error(f"Task {task_id} failed: {str(exc)}", exc_info=True)

        # Retry with exponential backoff
        retry_count = self.request.retries
        countdown = 60 * (2 ** retry_count)  # 60s, 120s, 240s

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=countdown)
        else:
            logger.error(f"Task {task_id} exhausted retries")
            return {
                "task_id": task_id,
                "user_id": user_id,
                "success": False,
                "error": str(exc),
                "retries_exhausted": True,
            }


@app.task(
    name='job_copilot.batch_analyze',
    bind=True,
)
def batch_analyze_applications_task(
    self,
    applications: list[dict[str, str]],
    batch_id: str | None = None,
) -> dict[str, object]:
    """
    Analyze multiple applications in batch.

    Args:
        applications: List of {"job_description": "...", "resume": "...", "user_id": "..."} dicts
        batch_id: Identifier for the batch

    Returns:
        Dictionary with batch results
    """
    task_id = self.request.id
    results = []

    logger.info(f"Starting batch task {task_id} with {len(applications)} applications")

    for i, app in enumerate(applications):
        try:
            # Queue individual analysis tasks
            task = analyze_application_task.delay(
                job_description=app.get("job_description", ""),
                resume=app.get("resume", ""),
                user_id=app.get("user_id"),
            )

            results.append({
                "index": i,
                "user_id": app.get("user_id"),
                "task_id": task.id,
                "status": "queued",
            })

            logger.debug(f"Queued subtask {task.id} for user {app.get('user_id')}")

        except Exception as e:
            logger.error(f"Failed to queue task for application {i}: {str(e)}")
            results.append({
                "index": i,
                "user_id": app.get("user_id"),
                "status": "failed",
                "error": str(e),
            })

    return {
        "batch_id": batch_id,
        "task_id": task_id,
        "total_applications": len(applications),
        "queued": sum(1 for r in results if r["status"] == "queued"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
        "results": results,
    }


@app.task(
    name='job_copilot.get_batch_results',
    bind=True,
)
def get_batch_results_task(
    _self,
    batch_id: str,
    task_ids: list[str],
) -> dict[str, object]:
    """
    Get results for a batch of tasks.

    Args:
        batch_id: Batch identifier
        task_ids: List of task IDs to retrieve

    Returns:
        Dictionary with combined results
    """
    from celery.result import AsyncResult  # type: ignore[import-untyped]

    results = []
    completed = 0
    failed = 0
    pending = 0

    for task_id in task_ids:
        result = AsyncResult(task_id, app=app)

        if result.ready():
            if result.successful():
                results.append({
                    "task_id": task_id,
                    "status": "completed",
                    "result": result.result,
                })
                completed += 1
            else:
                results.append({
                    "task_id": task_id,
                    "status": "failed",
                    "error": str(result.info),
                })
                failed += 1
        else:
            results.append({
                "task_id": task_id,
                "status": "pending",
            })
            pending += 1

    return {
        "batch_id": batch_id,
        "total": len(task_ids),
        "completed": completed,
        "failed": failed,
        "pending": pending,
        "results": results,
    }


# Periodic/scheduled tasks (if using Celery Beat)
# from celery.schedules import crontab
#
# app.conf.beat_schedule = {
#     'cleanup-expired-results': {
#         'task': 'job_copilot.cleanup_expired_results',
#         'schedule': crontab(hour=2, minute=0),  # 2 AM daily
#     },
# }
#
# @app.task(name='job_copilot.cleanup_expired_results')
# def cleanup_expired_results():
#     """Cleanup expired results from Redis."""
#     logger.info("Running cleanup task")
#     # Implement cleanup logic here


# Health check and monitoring
@app.task(name='job_copilot.health_check')
def health_check_task() -> dict[str, object]:
    """Health check task for monitoring."""
    try:
        init_llm()
        graph = get_job_copilot_graph()
        return {
            "status": "healthy",
            "llm_ready": True,
            "graph_ready": bool(graph),
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
        }


# Usage examples:
#
# 1. Single application analysis:
#    >>> task = analyze_application_task.delay(
#    ...     job_description="...",
#    ...     resume="...",
#    ...     user_id="user123"
#    ... )
#    >>> task.id  # Get task ID
#    >>> result = task.get()  # Wait for result
#
# 2. Batch analysis:
#    >>> applications = [
#    ...     {"job_description": "...", "resume": "...", "user_id": "user1"},
#    ...     {"job_description": "...", "resume": "...", "user_id": "user2"},
#    ... ]
#    >>> batch_task = batch_analyze_applications_task.delay(applications, batch_id="batch1")
#
# 3. Get batch results:
#    >>> get_batch_results_task.delay(batch_id="batch1", task_ids=[...])
#
# 4. Check task status:
#    >>> from celery.result import AsyncResult
#    >>> result = AsyncResult(task_id)
#    >>> result.status  # 'PENDING', 'STARTED', 'SUCCESS', 'FAILURE', etc.
#    >>> result.result  # Get result (waits if not ready)
