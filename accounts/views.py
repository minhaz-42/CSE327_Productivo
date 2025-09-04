from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
import json
from django.db.models import Count, Q   
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Student, Task, ScheduledTask
from django.utils.dateparse import parse_datetime
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from accounts.models import PlanYourTasks
from accounts.scheduler import run_scheduler
from django.core.exceptions import ValidationError
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from datetime import timedelta
from .scheduler import run_scheduler

# ------------------ PUBLIC VIEWS ------------------

def home(request):
    return render(request, "accounts/home.html")


def check_username(request):
    username = request.GET.get('username', '')
    exists = User.objects.filter(username__iexact=username).exists()
    return JsonResponse({'available': not exists})


def registration(request):
    context = {}
    if request.method == 'POST':
        firstname = request.POST.get('first-name')
        lastname = request.POST.get('last-name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        date_of_birth = request.POST.get('dob')
        institution = request.POST.get('university')
        profile_picture = request.FILES.get('profile_picture')

        if User.objects.filter(username=username).exists():
            context['error'] = "Username already taken."
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=firstname,
                last_name=lastname
            )
            Student.objects.create(
                user=user,
                dob=date_of_birth,
                institution=institution,
                profile_pic=profile_picture
            )
            context['success'] = "Registration successful! You can now log in."

    return render(request, "accounts/register.html", context)

##login logic
def login(request):
    context = {}
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            context['error'] = "Invalid username or password."

    return render(request, 'accounts/login.html', context)


##logout logic
def logout_view(request):
    logout(request)
    return redirect('home')


# ------------------ AUTHENTICATED VIEWS ------------------

@login_required(login_url='login')
def dashboard(request):
    user = request.user
    tasks = Task.objects.filter(user=user).order_by('end_time')

    #today = now().date()
    current_time = timezone.localtime();
    today = current_time.date();
    today_tasks = tasks.filter(end_time__date=today)
    today_tasks_incomplete = today_tasks.filter(end_time__gte=current_time,completed = False)
    task_rightnow = today_tasks_incomplete.filter( start_time__lte=current_time,end_time__gte=current_time).first();
    
    #for pomodoro logic calculating the time remaining for the task
    if task_rightnow:
        time_remaining_current_task = int((task_rightnow.end_time - current_time).total_seconds()) //1
    
    else:
        time_remaining_current_task = 0

    upcoming_tasks = tasks.filter(completed = False, end_time__date__gt=today)[:5]  # Limit to 5 upcoming tasks which are not completed
    
    next_task = None
    next_task_qs = None
    # next task
    if(today_tasks_incomplete):
        next_task_qs = today_tasks_incomplete.filter(
        Q(start_time__hour__gt=current_time.hour) | Q(start_time__hour=current_time.hour, start_time__minute__gt=current_time.minute)).order_by('start_time')  # earliest first
        
        
    if(next_task_qs):
        # Get the first upcoming task
        next_task = next_task_qs.first()
  

     
    #time remaining for next task
    if next_task:
       time_remaining = next_task.start_time - current_time
       total_seconds = int(time_remaining.total_seconds())
       total_seconds = total_seconds // 1
       hours = total_seconds // 3600
       minutes = (total_seconds % 3600) // 60
    # time_remaining is a timedelta object
    else:
       time_remaining = None
       hours = 0
       minutes = 0
       total_seconds = 0

    # Calculate statistics for dashboard
    completed_tasks_count = tasks.filter(completed=True).count()
    high_priority_count = tasks.filter(priority='high', completed=False).count()
    
    # Calculate productivity score (percentage of completed tasks)
    total_tasks = tasks.count()
    productivity_score = 0
    if total_tasks > 0:
        productivity_score = round((completed_tasks_count / total_tasks) * 100)

    # Get notifications for dashboard
    notifications = get_user_notifications(user)
    unread_count = sum(1 for notification in notifications if notification['unread'])

    context = {
        'today_tasks': today_tasks,
        'today_tasks_incomplete': today_tasks_incomplete,
        'next_task': next_task,
        'time_remaining_hours': hours,
        'time_remaining_minutes': minutes,
        'time_remaining_total_Seconds': total_seconds,
        'task_rightnow': task_rightnow,
        'time_remaining_current_task': time_remaining_current_task,
        'time_remaining': time_remaining,
        'upcoming_tasks': upcoming_tasks,
        'completed_tasks_count': completed_tasks_count,
        'high_priority_count': high_priority_count,
        'productivity_score': productivity_score,
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'accounts/index.html', context)

##adding task
@login_required
def task(request):
    """
    Render task page with both HTML tasks and JSON for JS.
    """
    user = request.user
    tasks = Task.objects.filter(user=user).order_by('-end_time')

    # Convert tasks to JSON with only needed fields for JS
    tasks_json_list = []
    for t in tasks:
        tasks_json_list.append({
            'pk': t.id,
            'fields': {
                'title': t.title,
                'description': t.description,
                'priority': t.priority,
                'category': t.category or 'none',
                'start_time': t.start_time.isoformat() if t.start_time else None,
                'end_time': t.end_time.isoformat() if t.end_time else None,
                'reminder': t.reminder or 'none',
                'completed': t.completed
            }
        })

    # Get notifications
    notifications = get_user_notifications(user)
    unread_count = sum(1 for notification in notifications if notification['unread'])

    context = {
        'tasks': tasks,
        'tasks_json': json.dumps(tasks_json_list),  # safely serialized for JS
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'accounts/tasks.html', context)


@login_required
def schedule(request):
    # Get notifications
    notifications = get_user_notifications(request.user)
    unread_count = sum(1 for notification in notifications if notification['unread'])
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'accounts/schedule.html', context)


@login_required
def task_events(request):
    # Only send NOT completed tasks
    qs = Task.objects.filter(user=request.user, completed=False)

    events = []
    for t in qs:
        start = t.start_time
        end = t.end_time or (start + timedelta(minutes=30))
        if timezone.is_aware(start): start = timezone.localtime(start)
        if timezone.is_aware(end):   end = timezone.localtime(end)
        priority = (t.priority or 'medium').lower()

        events.append({
            "id": t.id,
            "title": t.title,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "extendedProps": {
                "priority": priority,
                "category": t.category or 'none',
                "description": t.description or "",
            },
        })
    return JsonResponse(events, safe=False)


@login_required
def category(request):
    # Get notifications
    notifications = get_user_notifications(request.user)
    unread_count = sum(1 for notification in notifications if notification['unread'])
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'accounts/category.html', context)


@login_required
def settings(request):
    # Get notifications
    notifications = get_user_notifications(request.user)
    unread_count = sum(1 for notification in notifications if notification['unread'])
    
    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }
    return render(request, 'accounts/settings.html', context)


@login_required
def profile_update(request):
    context = {}
    if request.method == "POST":
        user = request.user
        student = user.student
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.save()

        if request.POST.get('remove_avatar') == 'true' and student.profile_pic:
            student.profile_pic.delete(save=False)
            student.profile_pic = None

        profile_pic = request.FILES.get('profile_pic')
        if profile_pic:
            student.profile_pic = profile_pic

        student.save()
        context['updated'] = "Profile updated successfully!"
    else:
        context['error'] = "Error in updating!"

    return render(request, "accounts/settings.html", context)


@login_required
def reset_password(request):
    context = {}
    if request.method == "POST":
        user = request.user
        current_password = request.POST.get('password')

        if user.check_password(current_password):
            new_pass = request.POST.get('new_password')
            user.set_password(new_pass)
            user.save()
            update_session_auth_hash(request, user)
            context['success'] = "Password changed successfully!"
        else:
            context['error'] = "Incorrect current password!"

    return render(request, "accounts/settings.html", context)


# ------------------ TASK FUNCTIONALITY ------------------

@login_required(login_url='login')
@csrf_exempt
def add_task(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))

            title = data.get('title')
            description = data.get('description', '')
            priority = data.get('priority', 'medium')
            category = data.get('category') or 'none'
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            reminder = data.get('reminder') or 'none'

            if not title or not start_time or not end_time:
                return JsonResponse({'success': False, 'error': 'Title and Start-time and End-time are required.'})
            
             # Check for time clash with existing tasks
            clash_exists = Task.objects.filter(
                user=request.user,
                start_time__lt=end_time,
                end_time__gt=start_time
            ).exists()

            if clash_exists:
                return JsonResponse({'success': False, 'error': 'Task timing clashes with an existing task.'})

            Task.objects.create(
                user=request.user,
                title=title,
                description=description,
                priority=priority,
                category=category,
                start_time=start_time,
                end_time=end_time,
                reminder=reminder
            )

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def edit_task(request, task_id):
    if request.method == 'POST':
        try:
            task = Task.objects.get(id=task_id, user=request.user)
            data = json.loads(request.body)

            new_start_time = parse_datetime(data.get('start_time')) or task.start_time
            new_end_time = parse_datetime(data.get('end_time')) or task.end_time

            # Check for time clash with other tasks (excluding current task)
            clash_exists = Task.objects.filter(
                user=request.user,
                start_time__lt=new_end_time,
                end_time__gt=new_start_time
            ).exclude(id=task.id).exists()

            if clash_exists:
                return JsonResponse({'success': False, 'error': 'Task timing clashes with another existing task.'})

            task.title = data.get('title', task.title)
            task.description = data.get('description', task.description)
            task.priority = data.get('priority', task.priority)
            task.category = data.get('category', task.category)
            task.start_time = new_start_time
            task.end_time = new_end_time
            task.reminder = data.get('reminder', task.reminder)
            task.save()

            return JsonResponse({'success': True})

        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})



@login_required
@csrf_exempt
def complete_task(request, task_id):
    if request.method == 'POST':
        try:
            task = Task.objects.get(pk=task_id, user=request.user)
            task.completed = True
            task.save()
            return JsonResponse({'success': True})
        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def delete_task(request, task_id):
    if request.method in ['POST', 'DELETE']:
        try:
            task = Task.objects.get(pk=task_id, user=request.user)
            task.delete()
            return JsonResponse({'success': True})
        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@csrf_exempt
def get_task(request, task_id):
    """Get task details for editing"""
    if request.method == 'GET':
        try:
            task = Task.objects.get(pk=task_id, user=request.user)
            return JsonResponse({
                'success': True,
                'task': {
                    'id': task.id,
                    'title': task.title,
                    'description': task.description,
                    'priority': task.priority,
                    'category': task.category,
                    'start_time': task.start_time.isoformat(),
                    'end_time': task.end_time.isoformat(),
                    'reminder': task.reminder,
                    'completed': task.completed
                }
            })
        except Task.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Task not found'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# ------------------ ANALYTICS & NOTIFICATIONS ------------------

@login_required
def analytics(request):
    # Get all tasks for the current user
    tasks = Task.objects.filter(user=request.user)
    total_tasks = tasks.count()
    
    # Calculate completed tasks
    completed_tasks = tasks.filter(completed=True).count()
    
    # Calculate in-progress tasks (not completed)
    in_progress_tasks = tasks.filter(completed=False).count()
    
    # Calculate overdue tasks (tasks not completed with end_time in the past)
    overdue_tasks = tasks.filter(completed=False, end_time__lt=timezone.now()).count()
    
    # Calculate completion rate (avoid division by zero)
    completion_rate = 0
    if total_tasks > 0:
        completion_rate = round((completed_tasks / total_tasks) * 100)
    
    # Calculate priority distribution
    high_priority_tasks = tasks.filter(priority='high').count()
    medium_priority_tasks = tasks.filter(priority='medium').count()
    low_priority_tasks = tasks.filter(priority='low').count()
    
    # Calculate priority percentages
    high_priority_percent = 0
    medium_priority_percent = 0
    low_priority_percent = 0
    
    if total_tasks > 0:
        high_priority_percent = round((high_priority_tasks / total_tasks) * 100)
        medium_priority_percent = round((medium_priority_tasks / total_tasks) * 100)
        low_priority_percent = round((low_priority_tasks / total_tasks) * 100)
    
    # Calculate status percentages
    in_progress_percent = 0
    overdue_percent = 0
    
    if total_tasks > 0:
        in_progress_percent = round((in_progress_tasks / total_tasks) * 100)
        overdue_percent = round((overdue_tasks / total_tasks) * 100)
    
    # Calculate high priority completion stats
    high_priority_completed = tasks.filter(priority='high', completed=True).count()
    high_priority_total = high_priority_tasks
    
    # Get time period from request (default to 'week')
    period = request.GET.get('period', 'week')
    
    # Generate data for charts based on selected period
    chart_data = generate_chart_data(request.user, period)
    
    # Get notifications for the user
    notifications = get_user_notifications(request.user)
    unread_count = sum(1 for notification in notifications if notification['unread'])
    
    context = {
        'completed_tasks': completed_tasks,
        'completion_rate': completion_rate,
        'in_progress_tasks': in_progress_tasks,
        'total_tasks': total_tasks,
        'overdue_tasks': overdue_tasks,
        'high_priority_percent': high_priority_percent,
        'medium_priority_percent': medium_priority_percent,
        'low_priority_percent': low_priority_percent,
        'in_progress_percent': in_progress_percent,
        'overdue_percent': overdue_percent,
        'high_priority_completed': high_priority_completed,
        'high_priority_total': high_priority_total,  # Fixed variable name
        'chart_data': chart_data,  # Pass the data object for template
        'chart_data_json': json.dumps(chart_data),  # For JavaScript charts
        'period': period,
        'notifications': notifications,
        'unread_count': unread_count,
    }
    
    return render(request, 'accounts/analytics.html', context)


def generate_chart_data(user, period):
    """Generate data for completion trend and priority distribution charts"""
    now = timezone.now()
    today = now.date()
    
    if period == 'week':
        # Last 7 days including today
        dates = []
        completion_trend = []
        
        for i in range(6, -1, -1):
            current_date = today - timedelta(days=i)
            dates.append(current_date.strftime('%a'))
            
            # Count tasks completed on this specific day
            count = Task.objects.filter(
                user=user,
                completed=True,
                end_time__date=current_date
            ).count()
            completion_trend.append(count)
            
    elif period == 'month':
        # Last 4 weeks (each week Monday to Sunday)
        dates = []
        completion_trend = []
        
        for i in range(4):
            week_end = today - timedelta(days=(i * 7))
            week_start = week_end - timedelta(days=6)
            dates.append(f'Wk {4-i}')
            
            # Count tasks completed in this week
            count = Task.objects.filter(
                user=user,
                completed=True,
                end_time__date__gte=week_start,
                end_time__date__lte=week_end
            ).count()
            completion_trend.append(count)
            
        # Reverse to show oldest to newest
        dates.reverse()
        completion_trend.reverse()
            
    elif period == 'quarter':
        # Last 3 months
        dates = []
        completion_trend = []
        
        for i in range(3):
            month_start = today - timedelta(days=(90 - (i * 30)))
            month_end = month_start + timedelta(days=29)
            dates.append(month_start.strftime('%b'))
            
            # Count tasks completed in this month
            count = Task.objects.filter(
                user=user,
                completed=True,
                end_time__date__gte=month_start,
                end_time__date__lte=month_end
            ).count()
            completion_trend.append(count)
            
    else:
        # Default to week
        dates = []
        completion_trend = []
        
        for i in range(6, -1, -1):
            current_date = today - timedelta(days=i)
            dates.append(current_date.strftime('%a'))
            
            count = Task.objects.filter(
                user=user,
                completed=True,
                end_time__date=current_date
            ).count()
            completion_trend.append(count)
    
    # Get priority distribution for ALL tasks (not just completed ones)
    priority_data = Task.objects.filter(user=user).values('priority').annotate(count=Count('id'))
    
    # Convert to dictionary format
    priority_dict = {item['priority']: item['count'] for item in priority_data}
    
    # Calculate percentages
    total_all_tasks = sum(priority_dict.values())
    priority_percentages = {
        'high': round((priority_dict.get('high', 0) / total_all_tasks * 100)) if total_all_tasks > 0 else 0,
        'medium': round((priority_dict.get('medium', 0) / total_all_tasks * 100)) if total_all_tasks > 0 else 0,
        'low': round((priority_dict.get('low', 0) / total_all_tasks * 100)) if total_all_tasks > 0 else 0,
    }
    
    return {
        'dates': dates,
        'completion_trend': completion_trend,
        'priority_data': priority_percentages,
        'total_period_tasks': sum(completion_trend),
    }


def get_user_notifications(user):
    """Generate real notifications based on user's tasks"""
    now = timezone.now()
    
    notifications = []
    
    # Get user's tasks
    tasks = Task.objects.filter(user=user)
    
    # 1. Due soon notifications (tasks due in next 24 hours)
    due_soon = tasks.filter(
        completed=False,
        end_time__gt=now,
        end_time__lte=now + timedelta(hours=24)
    )
    
    for task in due_soon:
        time_left = task.end_time - now
        hours_left = int(time_left.total_seconds() // 3600)
        
        notifications.append({
            'type': 'due_soon',
            'message': f'Task "{task.title}" is due in {hours_left} hours',
            'time': task.end_time,
            'unread': True,
            'icon': 'fas fa-tasks'
        })
    
    # 2. Overdue notifications
    overdue = tasks.filter(
        completed=False,
        end_time__lt=now
    )
    
    for task in overdue:
        notifications.append({
            'type': 'overdue',
            'message': f'Task "{task.title}" is overdue',
            'time': task.end_time,
            'unread': True,
            'icon': 'fas fa-exclamation-triangle'
        })
    
    # 3. Recent completions (tasks completed in last 24 hours)
    recent_completions = tasks.filter(
        completed=True,
        end_time__gte=now - timedelta(hours=24)
    )
    
    if recent_completions.count() > 0:
        notifications.append({
            'type': 'completion',
            'message': f'You completed {recent_completions.count()} tasks recently',
            'time': now,
            'unread': True,
            'icon': 'fas fa-check-circle'
        })
    
    # 4. Productivity insights
    total_tasks = tasks.count()
    completed_tasks = tasks.filter(completed=True).count()
    
    if total_tasks > 0:
        completion_rate = (completed_tasks / total_tasks) * 100
        if completion_rate > 75:
            notifications.append({
                'type': 'productivity',
                'message': f'Your productivity rate is {completion_rate:.1f}% - Great job!',
                'time': now,
                'unread': True,
                'icon': 'fas fa-chart-line'
            })
    
    # Sort notifications by time (newest first)
    notifications.sort(key=lambda x: x['time'], reverse=True)
    
    # Format time for display
    for notification in notifications:
        time_diff = now - notification['time']
        if time_diff.total_seconds() < 3600:  # Less than 1 hour
            minutes = int(time_diff.total_seconds() // 60)
            notification['time_display'] = f'{minutes} minutes ago'
        elif time_diff.total_seconds() < 86400:  # Less than 1 day
            hours = int(time_diff.total_seconds() // 3600)
            notification['time_display'] = f'{hours} hours ago'
        else:
            days = int(time_diff.total_seconds() // 86400)
            notification['time_display'] = f'{days} days ago'
    
    return notifications


@login_required
@csrf_exempt
def mark_notifications_read(request):
    if request.method == 'POST':
        # In a real application, you would update a Notification model
        # to mark notifications as read for this user
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})


##just for testing
#@login_required(login_url='login')
#def schedule_plan(request, plan_id):
 #   plan = get_object_or_404(PlanYourTasks, id=plan_id)

  #  try:
   #     run_scheduler(plan)
    #    messages.success(request, "Tasks scheduled successfully!")
    #except ValidationError as e:
     #   messages.error(request, str(e))

    # Redirect to admin ScheduledTask list for now
    #return redirect("/admin/accounts/scheduledtask/")



# accounts/views.py
from django.shortcuts import render


@login_required
def save_preferences(request):
     if request.method == "POST":
        try:
            date_str = request.POST.get("date")
            start_time_str = request.POST.get("start_time")
            end_time_str = request.POST.get("end_time")

            if not date_str or not start_time_str or not end_time_str:
                return JsonResponse({"success": False, "error": "All fields are required."})

            date = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time = datetime.strptime(start_time_str, "%H:%M").time()
            end_time = datetime.strptime(end_time_str, "%H:%M").time()

            # create or update the plan for that user + date
            plan, created = PlanYourTasks.objects.update_or_create(
                user=request.user,
                date=date,
                defaults={
                    "preferred_start_time": start_time,
                    "preferred_end_time": end_time,
                }
            )

            return JsonResponse({"success": True, "message": "Preferences saved!"})

        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

     return JsonResponse({"success": False, "error": "Invalid request method"})

@login_required
@csrf_exempt
def add_plantask(request):
    if request.method == 'POST':
        try:
            # Extract data from request
            plan_date_str = request.POST.get('plan_date')
            plan_start_str = request.POST.get('plan_start_time')
            plan_end_str = request.POST.get('plan_end_time')
            title = request.POST.get('title')
            description = request.POST.get('description', '')
            priority = request.POST.get('priority', 'medium')
            category = request.POST.get('category', 'none')
            duration_str = request.POST.get('duration')  # format: HH:MM
            start_time_str = request.POST.get('start_time')  # optional
            end_time_str = request.POST.get('end_time')      # optional
            reminder = request.POST.get('reminder', 'none')

            # Validate required fields
            if not (plan_date_str and plan_start_str and plan_end_str and title and duration_str):
                return JsonResponse({'success': False, 'error': 'Missing required fields.'})

            # Convert plan date and times to proper objects
            plan_date = datetime.strptime(plan_date_str, "%Y-%m-%d").date()
            plan_start_time = datetime.strptime(plan_start_str, "%H:%M").time()
            plan_end_time = datetime.strptime(plan_end_str, "%H:%M").time()

            # Get or create PlanYourTasks for the user
            plan, _ = PlanYourTasks.objects.get_or_create(
                user=request.user,
                date=plan_date,
                defaults={
                    'preferred_start_time': plan_start_time,
                    'preferred_end_time': plan_end_time
                }
            )

            # Convert duration string "HH:MM" to timedelta
            hours, minutes = map(int, duration_str.split(":"))
            duration = timedelta(hours=hours, minutes=minutes)

            # Convert optional start and end times
            start_time = datetime.strptime(start_time_str, "%H:%M").time() if start_time_str != "null" else None
            end_time = datetime.strptime(end_time_str, "%H:%M").time() if end_time_str != "null" else None

            # Create ScheduledTask
            ScheduledTask.objects.create(
                plan=plan,
                title=title,
                description=description,
                priority=priority,
                category=category,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
                reminder=reminder
            )

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def plan_your_tasks(request):
    # Get the selected date (e.g., from a GET parameter or default to today)
    date_str = request.GET.get('date')  # ?date=2025-09-04
    if date_str:
        selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
    else:
        selected_date = timezone.now().date()

    try:
        plan = PlanYourTasks.objects.get(user=request.user, date=selected_date)
        tasks = plan.tasks.all().order_by('start_time')  # related_name='tasks'
    except PlanYourTasks.DoesNotExist:
        tasks = []

    context = {
        'tasks': tasks,
        'selected_date': selected_date,
    }

    return render(request, 'planyourtask.html', context)


def auto_schedule(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            plan_date_str = data.get('plan_date')
            if not plan_date_str:
                return JsonResponse({'success': False, 'error': 'Missing plan date.'})

            plan_date = datetime.strptime(plan_date_str, "%Y-%m-%d").date()
            plan = PlanYourTasks.objects.get(user=request.user, date=plan_date)

            # Run scheduler (updates ScheduledTask start/end times)
            updated_tasks = run_scheduler(plan)

            # Serialize scheduled tasks
            tasks_data = []
            for t in updated_tasks:
                tasks_data.append({
                    'id': t.id,
                    'title': t.title,
                    'description': t.description,
                    'priority': t.priority,
                    'category': t.category,
                    'start_time': t.start_time.strftime("%H:%M") if t.start_time else "",
                    'end_time': t.end_time.strftime("%H:%M") if t.end_time else "",
                    'duration': str(t.duration) if t.duration else "",
                    'reminder': getattr(t, 'reminder', ''),
                })

            return JsonResponse({'success': True, 'tasks': tasks_data})

        except PlanYourTasks.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'No plan found for that date.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})