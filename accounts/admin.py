from django.contrib import admin
from django.apps import apps
from .models import Task

# Register your models here.

#Connecting my models to the admin  panel so that I can view them for there
app = apps.get_app_config('accounts')  

for model_name, model in app.models.items():
    if model is Task:
        continue
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass  # ignore if already registered

class TaskAdmin(admin.ModelAdmin):
    list_display = ('title','user','priority', 'category','start_time','end_time','completed')

admin.site.register(Task, TaskAdmin)