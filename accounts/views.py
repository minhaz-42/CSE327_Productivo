from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.decorators import login_required
from .models import Student
# Create your views here.

def home(request):
    return render(request,"accounts/home.html")

def check_username(request):
    username = request.GET.get('username', '')
    exists = User.objects.filter(username__iexact=username).exists()
    return JsonResponse({'available': not exists})

def registration(request):
     #error = None
     #success = None
     context = {}  #creating context dictionary
     if request.method == 'POST':
        firstname = request.POST.get('first-name')
        lastname = request.POST.get('last-name')
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        date_of_birth = request.POST.get('dob')
        institution = request.POST.get('university')
        profile_picture = request.FILES.get('profile_picture')

        if User.objects.filter(username = username).exists():
            context['error'] = "Username already taken."
            #return redirect('registration')  # stay on registration page

        else:
            user = User.objects.create_user(first_name = firstname, last_name= lastname, username=username, email = email, password=password)
            Student.objects.create(
                user=user,
                dob=date_of_birth,
                institution = institution,
                profile_pic =profile_picture,
            )

            #sending mail to uer
            
           ## send_mail(
             ##   'Productivo Registration Successful',
               ## f'Thank you @{username} for registering in Productivo. Get ready to manage your works efficiently.',
                ##'zuhayer.islam@northsouth.edu',  # my gmail address
                #[email],
                #fail_silently=False, #stop process if error occurs
            #)
            context['success'] = "Registration successful! You can now log in."
          

     return render(request,"accounts/register.html", context)

def login(request):
    context = {}  #context dictionary

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user) 
            context['success'] = "Login Successful"
            
        else:
            context['error'] = "Invalid username or password."

    return render(request, 'accounts/login.html', context)

@login_required
def dashboard(request):
    return render(request, 'accounts/index.html')

def task(request):
    return render(request, 'accounts/tasks.html')

def schedule(request):
    return render(request, 'accounts/schedule.html')

def category(request):
    return render(request, 'accounts/category.html')

def analytics(request):
    return render(request, 'accounts/analytics.html')

def settings(request):
    return render(request, 'accounts/settings.html')



