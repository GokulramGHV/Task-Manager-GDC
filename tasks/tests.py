from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from .models import Task, STATUS_CHOICES, History, EmailSettings
from .views import (
    GenericAllTasksView,
    GenericCompletedTaskView,
    GenericTaskCreateView,
    GenericTaskView,
)
from rest_framework.test import APIClient
from .tasks import send_email_reminder
from django.utils import timezone
from django.core import mail


class Tests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="gokul", email="gokul@ghv.org", password="abcd@123"
        )
        self.test_task = Task.objects.create(
            title="TaskTest",
            description="Nisl tincidunt eget nullam non nisi est sit amet",
            completed=False,
            deleted=False,
            priority=1,
            user=self.user,
        )
        self.test_task.save()

    def test_pending_tasks_view(self):
        request = self.factory.get("/tasks")
        request.user = self.user
        response = GenericTaskView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_all_tasks_view(self):
        request = self.factory.get("/tasks")
        request.user = self.user
        response = GenericAllTasksView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_completed_tasks_view(self):
        request = self.factory.get("/tasks")
        request.user = self.user
        response = GenericCompletedTaskView.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_user_login(self):
        response = self.client.get("/user/login/")
        self.assertEqual(response.status_code, 200)

    def test_user_signup(self):
        response = self.client.get("/user/signup/")
        self.assertEqual(response.status_code, 200)

    def test_unauthorized_views(self):
        urls = ("/tasks/","/all_tasks/","/completed_tasks/","/create-task/")
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.url, "/user/login?next="+url)

    def test_create_task(self):
        self.client.login(username="gokul", password="abcd@123")
        response = self.client.post(
            "/create-task/",
            {
                "title": "Task1",
                "description": "Lorem ipsum dolor sit amet",
                "priority": 1,
                "completed": False,
                "status": STATUS_CHOICES[0][0],
            },
        )
        self.assertEqual(response.status_code, 302)

    def test_update_task(self):
        self.client.login(username="gokul", password="abcd@123")
        response = self.client.post(
            f"/update-task/{self.test_task.pk}/",
            {
                "title": "TestTask",
                "description": "Lorem Ipsum",
                "priority": 1,
                "completed": False,
                "status": STATUS_CHOICES[0][0],
            },
        )
        self.assertEqual(response.status_code, 302)
        updated_task = Task.objects.get(id=self.test_task.id)
        self.assertEqual(updated_task.description, "Lorem Ipsum")

    def test_task_detail(self):
        self.client.login(username="gokul", password="abcd@123")
        response = self.client.get(f"/detail-task/{self.test_task.pk}/")
        self.assertEqual(response.status_code, 200)

    def test_complete_task(self):
        self.client.login(username="gokul", password="abcd@123")
        response = self.client.post(f"/complete_task/{self.test_task.pk}/")
        self.assertEqual(response.status_code, 302)
        task1 = Task.objects.get(id=self.test_task.pk)
        self.assertEqual(task1.completed, True)
        

    def test_delete_task(self):
        self.client.login(username="gokul", password="abcd@123")
        response = self.client.post(f"/delete-task/{self.test_task.id}/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Task.objects.filter(id=self.test_task.id).exists(), False)


class APITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="gokul", email="gokul@ghv.org", password="abcd@123"
        )
        self.test_task = Task.objects.create(
            title="TaskTest",
            description="Nisl tincidunt eget nullam non nisi est sit amet",
            completed=False,
            deleted=False,
            priority=1,
            user=self.user,
        )
        self.test_task.save()

    def test_api_task_list(self):
        self.client.login(username="gokul", password="abcd@123")
        response = self.client.get("/api/v1/task/")
        self.assertEqual(response.status_code, 200)

    def test_api_task_instance(self):
        self.client.login(username="gokul", password="abcd@123")
        response = self.client.get(f"/api/v1/task/{self.test_task.id}/")
        self.assertEqual(response.status_code, 200)

    def test_api_task_history(self):
        self.client.login(username="gokul", password="abcd@123")
        response = self.client.get(f"/api/v1/task/{self.test_task.id}/history/")
        self.assertEqual(response.status_code, 200)

    def test_api_task_history_instance(self):
        self.client.login(username="gokul", password="abcd@123")
        self.test_task.status = STATUS_CHOICES[2][0]
        self.test_task.save()
        response = self.client.get(f"/api/v1/task/{self.test_task.id}/history/")

        self.assertIn("PENDING", response.json()[0].values())  # Previous value
        self.assertIn("COMPLETED", response.json()[0].values())  # Updated value

    def test_api_task_delete(self):
        self.client.login(username="gokul", password="abcd@123")
        task = Task.objects.create(
            title="Task7", description="Lorem", user=self.user, priority=3
        )
        response = self.client.delete(f"/api/v1/task/{task.id}/")
        self.assertEqual(Task.objects.filter(id=task.id).exists(), False)
        self.assertEqual(response.status_code, 204)

    def test_unauthorized_api_views(self):
        response = self.client.get("/api/v1/task/")
        self.assertEqual(response.status_code, 403)
        response = self.client.get("/api/v1/task/1/")
        self.assertEqual(response.status_code, 403)
        response = self.client.get("/api/v1/task/1/history/")
        self.assertEqual(response.status_code, 403)


class CeleryTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="gokul", email="gokul@ghv.org", password="abcd@123"
        )
        Task.objects.create(
            title="TaskTest",
            description="Nisl tincidunt eget nullam non nisi est sit amet",
            completed=False,
            deleted=False,
            priority=1,
            user=self.user,
        ).save()
        EmailSettings.objects.create(
            user=self.user, email_time=timezone.now(), email_date=timezone.now()
        )

    def test_mail_remainder(self):
        send_email_reminder()
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(
            "Task Report\nHere's your report for today:\nPENDING: 1\nIN_PROGRESS: 0\nCOMPLETED: 0\nCANCELLED: 0\n",
            mail.outbox[0].body,
        )
