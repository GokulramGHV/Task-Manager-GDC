from datetime import timedelta

from celery.decorators import periodic_task
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
from task_manager.celery import app
from django.conf import settings

from tasks.models import STATUS_CHOICES, EmailSettings, Task


@periodic_task(run_every=timedelta(seconds=30))
def send_email_reminder():
    print("Starting to process email")
    email_qs = EmailSettings.objects.filter(
        email_enable=True,
        email_time__lte=timezone.now(),
        email_date__lte=timezone.now(),
    )
    for email in email_qs:
        email_content = "Task Report\nHere's your report for today:\n"
        user = User.objects.get(id=email.user.id)
        pending_qs = Task.objects.filter(user=user, completed=False, deleted=False)
        for status in STATUS_CHOICES:
            count = pending_qs.filter(status=status[0]).count()
            email_content += f"{status[0]}: {count}\n"

        send_mail(
            "Task Report (Breakdown based on task status)",
            email_content,
            settings.EMAIL_HOST_USER,
            [user.email],
        )
        print("Completed Processing for User", user.username, user.id)

        email.email_date += timedelta(days=1)
        email.save()
