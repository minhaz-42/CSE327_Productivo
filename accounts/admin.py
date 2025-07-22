from django.contrib import admin
from django.apps import apps

# Register your models here.

#Connecting my models to the admin  panel so that I can view them for there
app = apps.get_app_config('accounts')  

for model_name, model in app.models.items():
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        pass  # ignore if already registered

