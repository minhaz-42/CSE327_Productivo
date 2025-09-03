from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name="home"),
    path('register/', views.registration, name="registration"),
    path('login/', views.login, name="login"),
    path('check-username/', views.check_username, name="check-username"),
    path('index/', views.dashboard, name="dashboard"),
    path('task/', views.task, name="task"),
    path('schedule/', views.schedule, name="schedule"),
    path('analytics/', views.analytics, name="analytics"),
    path('category/', views.category, name="category"),
    path('settings/', views.settings, name="settings"),
    path('logout/', views.logout_view, name="logout"),
    path('profile_update/', views.profile_update, name="profile_update"),
    path('reset_password/', views.reset_password, name="reset_password"),
    path('schedule-plan/<int:plan_id>/', views.schedule_plan, name='schedule_plan'),
    
    # Task management
    path('add-task/', views.add_task, name='add-task'),
    path('edit-task/<int:task_id>/', views.edit_task, name='edit-task'),
    path('complete-task/<int:task_id>/', views.complete_task, name='complete-task'),
    path('delete-task/<int:task_id>/', views.delete_task, name='delete-task'),
    path('analytics/', views.analytics, name="analytics"),
    path('mark-notifications-read/', views.mark_notifications_read, name='mark_notifications_read'),
    


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
