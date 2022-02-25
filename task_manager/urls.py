"""task_manager URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path
from tasks.views import *
from tasks.apiviews import *
from rest_framework_nested.routers import SimpleRouter, NestedSimpleRouter

router = SimpleRouter()
router.register(r"api/v1/task", TaskViewSet)
nested_router = NestedSimpleRouter(router, r"api/v1/task", lookup="task")
nested_router.register("history", HistoryViewSet, basename="task-history")

urlpatterns = (
    [
        path("", RedirectRootToTasks.as_view()),
        path("admin/", admin.site.urls),
        path("taskapi", TaskListAPI.as_view()),
        path("tasks/", GenericTaskView.as_view()),
        path("user/signup/", UserCreateView.as_view()),
        path("user/login/", UserLoginView.as_view()),
        path("user/logout/", LogoutView.as_view()),
        path("create-task/", GenericTaskCreateView.as_view()),
        path("update-task/<pk>/", GenericTaskUpdateView.as_view()),
        path("detail-task/<pk>/", GenericTaskDetailView.as_view()),
        path("delete-task/<pk>/", GenericTaskDeleteView.as_view()),
        path("completed_tasks/", GenericCompletedTaskView.as_view()),
        path("complete_task/<pk>/", GenericCompleteTaskView.as_view()),
        path("all_tasks/", GenericAllTasksView.as_view()),
        path("settings/<pk>/", EmailSettingsView.as_view()),
        # path("sample/", send_email_view),
    ]
    + router.urls
    + nested_router.urls
)
