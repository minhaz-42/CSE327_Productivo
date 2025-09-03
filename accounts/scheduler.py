from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from collections import Counter
from accounts.models import PlanYourTasks, ScheduledTask, Task

PRIORITY_ORDER = {"high": 1, "medium": 2, "low": 3}

def run_scheduler(plan: PlanYourTasks):
    tasks = list(plan.tasks.all())
    if not tasks:
        raise ValidationError("No tasks found for this plan.")

    user = plan.user

    # --- Step 1: Separate fixed and flexible tasks ---
    fixed_tasks = sorted(
        [t for t in tasks if t.start_time and t.end_time],
        key=lambda t: t.start_time
    )
    flexible_tasks = [t for t in tasks if not t.start_time or not t.end_time]

    # --- Step 2: Sort flexible tasks by priority -> SJF ---
    flexible_tasks.sort(
        key=lambda t: (
            PRIORITY_ORDER.get(t.priority, 3),
            t.duration.total_seconds() if t.duration else float("inf")
        )
    )

    # --- Step 3: Collect historical completion data ---
    completed_tasks = Task.objects.filter(user=user, completed=True)
    completion_hours = [t.end_time.hour for t in completed_tasks if t.end_time]
    hour_counts = Counter(completion_hours)  # e.g., {10:5, 14:3, 16:2}

    # --- Step 4: Build available gaps from fixed tasks ---
    start_dt = datetime.combine(plan.date, plan.preferred_start_time)
    end_dt = datetime.combine(plan.date, plan.preferred_end_time)
    gaps = []
    current_time = start_dt

    for ft in fixed_tasks:
        ft_start = datetime.combine(plan.date, ft.start_time)
        ft_end = datetime.combine(plan.date, ft.end_time)

        if ft_start < current_time:
            raise ValidationError(f"Fixed task '{ft.title}' overlaps previous schedule.")

        if ft_start > current_time:
            gaps.append((current_time, ft_start))

        current_time = ft_end

    if current_time < end_dt:
        gaps.append((current_time, end_dt))

    # --- Step 5: Schedule flexible tasks in gaps using preferred hours ---
    for task in flexible_tasks:
        if not task.duration:
            raise ValidationError(f"Task '{task.title}' has no duration.")

        # Sort gaps by how many tasks were historically completed in that hour
        gaps_sorted = sorted(
            gaps,
            key=lambda g: -hour_counts.get(g[0].hour, 0)  # higher count = higher priority
        )

        scheduled = False
        for i, (gap_start, gap_end) in enumerate(gaps_sorted):
            task_end = gap_start + task.duration
            if task_end <= gap_end:
                # Fits in this gap
                task.start_time = gap_start.time()
                task.end_time = task_end.time()
                task.save()

                # Update the gap
                if task_end < gap_end:
                    gaps[i] = (task_end, gap_end)
                else:
                    gaps.pop(i)
                scheduled = True
                break

        if not scheduled:
            raise ValidationError(f"Task '{task.title}' cannot fit in the available time window.")

    return tasks
