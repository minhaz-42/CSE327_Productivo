from datetime import datetime, timedelta
from django.core.exceptions import ValidationError
from collections import Counter
from accounts.models import PlanYourTasks, ScheduledTask, Task

PRIORITY_ORDER = {"high": 1, "medium": 2, "low": 3}  #ranking priorities to make sorting easier

def run_scheduler(plan: PlanYourTasks):
    tasks = list(plan.tasks.all())  #retrieve tasks from planned task
    if not tasks:
        raise ValidationError("No tasks found for this plan.") #raise error if no tasks planned

    user = plan.user

    # --- Separating fixed and flexible tasks 
    fixed_tasks = sorted(
        [t for t in tasks if t.start_time and t.end_time], #seperate fixed tasks 
        key=lambda t: t.start_time
    )
    flexible_tasks = [t for t in tasks if not t.start_time or not t.end_time]   #seperate flexible tasks

    # --- Sorting flexible tasks by priority then SJF
    flexible_tasks.sort(
        key=lambda t: (
            PRIORITY_ORDER.get(t.priority, 3),
            t.duration.total_seconds() if t.duration else float("inf")
        )
    ) #flexible tasks are sorted by priority and then by duration to break tie

    # Collect historical completion data 
    completed_tasks = Task.objects.filter(user=user, completed=True)
    completion_hours = [t.end_time.hour for t in completed_tasks if t.end_time] #finding the hours at which the tasks were previously completed
    hour_counts = Counter(completion_hours)  #maps each end time to the frequency of completion

    # Building available gaps from fixed tasks 
    start_dt = datetime.combine(plan.date, plan.preferred_start_time)
    end_dt = datetime.combine(plan.date, plan.preferred_end_time)
    gaps = []
    current_time = start_dt   ##move current_time to the start date

    for ft in fixed_tasks:
        ft_start = datetime.combine(plan.date, ft.start_time)     ##for each fixed task their start time is as defined
        ft_end = datetime.combine(plan.date, ft.end_time)         ##their end time is as defined

        if ft_start < current_time:
            raise ValidationError(f"Fixed task '{ft.title}' overlaps previous schedule.")  #if any task starts before the preffered time then error

        if ft_start > current_time:
            gaps.append((current_time, ft_start))   #if a task starts after start time then append to create a gap

        current_time = ft_end  #moves current time to the curren tasks end time

    if current_time < end_dt:
        gaps.append((current_time, end_dt))  #creates another gap from current time to the end

    # Schedule flexible tasks in gaps using preferred hours 
    for task in flexible_tasks:
        if not task.duration:
            raise ValidationError(f"Task '{task.title}' has no duration.")   #flexible tasks must have duration

        # Sort gaps by how many tasks were historically completed in that hour
        gaps_sorted = sorted(
            gaps,
            key=lambda g: -hour_counts.get(g[0].hour, 0)  # higher count = higher priority
        )

        #logic to schedule tasks which are flexible
        scheduled = False
        for i, (gap_start, gap_end) in enumerate(gaps_sorted):
            task_end = gap_start + task.duration
            if task_end <= gap_end:   #if the task fits in the gap 
                # Fits in this gap
                task.start_time = gap_start.time()
                task.end_time = task_end.time()
                task.save()  #then save the task

                # Update the gap
                if task_end < gap_end:
                    gaps[i] = (task_end, gap_end) 
                else:
                    gaps.pop(i)           #remove the gap
                scheduled = True
                break

        if not scheduled:
            raise ValidationError(f"Task '{task.title}' cannot fit in the available time window.")  #if any task couldnt be fit

    return tasks
