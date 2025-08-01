from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.utils.timezone import now
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Student, Task


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


def logout_view(request):
    logout(request)
    return redirect('home')


# ------------------ AUTHENTICATED VIEWS ------------------

@login_required(login_url='login')
def dashboard(request):
    user = request.user
    tasks = Task.objects.filter(user=user).order_by('deadline')

    today = now().date()
    today_tasks = tasks.filter(deadline__date=today)
    upcoming_tasks = tasks.exclude(deadline__date=today)

    context = {
        'today_tasks': today_tasks,
        'upcoming_tasks': upcoming_tasks,
    }
    return render(request, 'accounts/index.html', context)


@login_required
def task(request):
    return render(request, 'accounts/tasks.html')


@login_required
def schedule(request):
    return render(request, 'accounts/schedule.html')


@login_required
def category(request):
    return render(request, 'accounts/category.html')


@login_required
def analytics(request):
    return render(request, 'accounts/analytics.html')


@login_required
def settings(request):
    return render(request, 'accounts/settings.html')


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
@csrf_exempt  # Required if CSRF token is not included in fetch header
def add_task(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))

            title = data.get('title')
            description = data.get('description', '')
            priority = data.get('priority', 'medium')
            category = data.get('category') or 'none'
            deadline = data.get('deadline')
            reminder = data.get('reminder') or 'none'

            if not title or not deadline:
                return JsonResponse({'success': False, 'error': 'Title and deadline are required.'})

            Task.objects.create(
                user=request.user,
                title=title,
                description=description,
                priority=priority,
                category=category,
                deadline=deadline,
                reminder=reminder
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def task(request):
    user = request.user
    tasks = Task.objects.filter(user=user).order_by('-deadline')  # or any other sorting you want
    context = {
        'tasks': tasks
    }
    return render(request, 'accounts/tasks.html', context)
