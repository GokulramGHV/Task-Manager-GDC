from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import datetime


STATUS_CHOICES = (
    ("PENDING", "PENDING"),
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("COMPLETED", "COMPLETED"),
    ("CANCELLED", "CANCELLED"),
)


class Task(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    completed = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)
    priority = models.IntegerField()
    status = models.CharField(
        max_length=100, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0]
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(priority__gt=0), name="priority_gt_0")
        ]

    def __str__(self):
        return self.title


class EmailSettings(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    email_time = models.TimeField(editable=True, default=timezone.now)
    email_date = models.DateField(default=timezone.now)
    email_enable = models.BooleanField(default=True)


class History(models.Model):
    prev_status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0]
    )
    updated_status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, default=STATUS_CHOICES[0][0]
    )
    changed_date = models.DateField(auto_now=True)
    task_changed = models.ForeignKey(
        Task, on_delete=models.CASCADE, null=True, blank=True
    )


@receiver(pre_save, sender=Task)
def generate_history(sender, instance, **kwargs):
    if Task.objects.filter(pk=instance.id).exists():
        prev_task = Task.objects.get(pk=instance.id)
        if instance.status == prev_task.status:
            return
        History(
            prev_status=prev_task.status,
            updated_status=instance.status,
            task_changed=instance,
        ).save()
