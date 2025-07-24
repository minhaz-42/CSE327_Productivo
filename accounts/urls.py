from django.urls import path, include
from . import views

urlpatterns = [
   
   path('', views.home, name = "home"),
   path('register/', views.registration, name = "registration"),
   path('login/', views.login, name = "login"),
   path('check-username/', views.check_username, name = "check-username"),
   path('index/', views.dashboard, name = "dashboard"),
   path('task/', views.task, name = "task"),
   path('schedule/', views.schedule, name = "schedule"),
   path('analytics/', views.analytics, name = "analytics"),
   path('category/', views.category, name = "category"),
   path('settings/', views.settings, name = "settings"),

   
]
