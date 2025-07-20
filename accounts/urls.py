from django.urls import path, include
from . import views

urlpatterns = [
   
   path('', views.home, name = "home"),
   path('register/', views.registration, name = "registration"),
   path('login/', views.login, name = "login"),
   
]
