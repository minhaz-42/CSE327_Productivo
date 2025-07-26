from pyexpat.errors import messages
from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login as auth_login, logout,update_session_auth_hash
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

@login_required(login_url= 'login')
def dashboard(request):
    return render(request, 'accounts/index.html')

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


def logout_view(request):
    logout(request)
    return redirect('home')

def profile_update(request):
     
     context = {}  ##context dictionary
     if request.method == "POST":
         user = request.user
         student = user.student
         user.first_name = request.POST.get('first_name', user.first_name)
         user.last_name = request.POST.get('last_name', user.last_name)
         user.email = request.POST.get('email', user.email)
         user.save()

        #remove avatar 
         if request.POST.get('remove_avatar') == 'true':
             if student.profile_pic:
                student.profile_pic.delete(save=False)  # delete file
                student.profile_pic = None
                student.save()
            
        #store profile pic
         profile_pic = request.FILES.get('profile_pic')
         if(profile_pic):
              student.profile_pic = profile_pic
              student.save()

         context['updated'] = "Profile Updated Successfully!"
    
   
     else:
         context['error'] = "Error in updating!"

     return render(request, "accounts/settings.html", context)

def reset_password(request):
      context = {} #context dictinary

      if request.method == "POST":
        user = request.user
        current_password = request.POST.get('password')

        if user.check_password(current_password):
           new_pass = request.POST.get('new_password')
           user.set_password(new_pass)
           user.save()

           update_session_auth_hash(request, user)
           context['success'] = "Password changed successfull!"
        
    
      
         
        context['error'] = "Error in changing password!"

      return render(request, "accounts/settings.html", context)
