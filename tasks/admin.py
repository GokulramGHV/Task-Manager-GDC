from django.contrib import admin

# Register your models here.

from tasks.models import Task

admin.sites.site.register(Task)
