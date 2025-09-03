from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from accounts.models import PlanYourTasks, ScheduledTask

# Define order of priorities
PRIORITY_ORDER = {"high": 1, "medium": 2, "low": 3}

def run_scheduler(plan: PlanYourTasks):
    """
    Schedule all tasks in a given PlanYourTasks based on:
    1. Priority
    2. Shortest Job First (duration)
    Raises ValidationError if tasks cannot fit in the given interval.
    """
    tasks = list(plan.tasks.all())  # get ScheduledTask for this plan

    if not tasks:
        raise ValidationError("No tasks found for this plan.")

    # Sort tasks: first by priority, then by duration
    tasks.sort(
        key=lambda t: (
            PRIORITY_ORDER.get(t.priority, 3),
            t.duration.total_seconds() if t.duration else float("inf")
        )
    )

    # Convert preferred start and end time to datetime objects
    start_dt = datetime.combine(plan.date, plan.preferred_start_time)
    end_dt = datetime.combine(plan.date, plan.preferred_end_time)

    current_time = start_dt

    for task in tasks:
        if not task.duration:
            raise ValidationError(f"Task '{task.title}' has no duration.")

        task_end = current_time + task.duration

        # Check if task fits
        if task_end > end_dt:
            raise ValidationError(
                f"Task '{task.title}' cannot fit in the available time window."
            )

        # Save scheduled times
        task.start_time = current_time.time()
        task.end_time = task_end.time()
        task.save()

        # Move current time forward
        current_time = task_end

    return tasks
