# Add your Views Here
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import ModelForm
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views import View
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import CreateView, DeleteView, DeletionMixin, UpdateView
from django.views.generic.list import ListView
from django.core.mail import send_mail
from django.conf import settings

from tasks.forms import *
from tasks.models import Task, EmailSettings


class TaskCompletedCount:
    def get_context_data(self, *args, **kwargs):
        base_qs = Task.objects.filter(user=self.request.user)
        active_tasks = base_qs.filter(deleted=False)
        completed_tasks = active_tasks.filter(completed=True)
        context = super().get_context_data(*args, **kwargs)
        context["completed_count"] = completed_tasks.count()
        context["total_count"] = active_tasks.count()
        return context


class RedirectRootToTasks(RedirectView):
    url = "/tasks"


class AuthorisedTaskManager(LoginRequiredMixin):
    def get_queryset(self):
        return Task.objects.filter(deleted=False, user=self.request.user).order_by(
            "priority"
        )


class UserLoginView(LoginView):
    form_class = CustomUserLoginForm
    template_name = "user_login.html"


class UserCreateView(CreateView):
    form_class = CustomUserCreateForm
    template_name = "user_create.html"
    success_url = "/user/login"

    def form_valid(self, form):
        self.object = form.save()
        self.object.save()
        EmailSettings(user=self.object).save()
        return HttpResponseRedirect(self.get_success_url())


class EmailSettingsView(UpdateView):
    model = EmailSettings
    form_class = EmailSettingsForm
    template_name = "email_settings.html"
    success_url = "/tasks"


class GenericCompleteTaskView(AuthorisedTaskManager, View, SingleObjectMixin):
    success_url = "/tasks"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        Task.objects.filter(id=self.object.id, user=self.request.user).update(
            completed=True
        )
        return HttpResponseRedirect(self.success_url)


class GenericAllTasksView(TaskCompletedCount, AuthorisedTaskManager, ListView):
    template_name = "all_tasks.html"
    context_object_name = "tasks"
    paginate_by = 4


class GenericTaskDeleteView(AuthorisedTaskManager, DeleteView):
    model = Task
    template_name = "task_delete.html"
    success_url = "/tasks"


class GenericTaskDetailView(AuthorisedTaskManager, DetailView):
    model = Task
    template_name = "task_detail.html"


@transaction.atomic
def task_priority_check(priority, user):
    """
    A function to check if any two tasks have the same priority
    if so, then cascade update the priorities such that no two tasks have the same priority
    """

    task_lst = (
        Task.objects.select_for_update()
        .filter(
            deleted=False,
            user=user,
            completed=False,
            priority__gte=priority,
        )
        .order_by("priority")
    )

    update_lst = []

    for task in task_lst:
        if task.priority != priority:
            break
        task.priority += 1
        priority += 1
        update_lst.append(task)

    Task.objects.bulk_update(update_lst, ["priority"])


class TaskFormValidMixin:
    def form_valid(self, form):
        priority = form.cleaned_data["priority"]
        if form.cleaned_data["completed"] == False:
            if form.has_changed() and "priority" in form.changed_data:
                task_priority_check(priority, self.request.user)
        self.object = form.save()
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class GenericTaskCreateView(TaskFormValidMixin, LoginRequiredMixin, CreateView):
    form_class = TaskCreateForm
    template_name = "task_create.html"
    success_url = "/tasks"


class GenericTaskUpdateView(TaskFormValidMixin, AuthorisedTaskManager, UpdateView):
    model = Task
    form_class = TaskCreateForm
    template_name = "task_update.html"
    success_url = "/tasks"


class GenericCompletedTaskView(TaskCompletedCount, LoginRequiredMixin, ListView):
    template_name = "completed.html"
    context_object_name = "tasks"
    paginate_by = 4

    def get_queryset(self):
        return Task.objects.filter(completed=True, user=self.request.user).order_by(
            "priority"
        )


class GenericTaskView(TaskCompletedCount, LoginRequiredMixin, ListView):
    template_name = "tasks.html"
    context_object_name = "tasks"
    paginate_by = 4

    def get_queryset(self):
        base_qs = Task.objects.filter(user=self.request.user)
        active_tasks = base_qs.filter(deleted=False, completed=False).order_by(
            "priority"
        )
        return active_tasks
