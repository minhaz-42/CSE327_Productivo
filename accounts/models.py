from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

PRIORITY_CHOICES = [('low', 'Low'),('medium', 'Medium'),('high', 'High'),]

REMINDER_CHOICES = [('none', 'None'),('15', '15 minutes before'),('30', '30 minutes before'),('60', '1 hour before'),('1440', '1 day before'),]

CATEGORY_CHOICES = [ ('none', 'None'),('work', 'Work'),('personal', 'Personal'),('finance', 'Finance'),('health', 'Health'),('study', 'Study'),('other', 'Other'),]

# ------------------
# Student Model
# ------------------
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)   # Each student linked to a user
    dob = models.DateField()
    institution = models.CharField(max_length=255)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.username



# ------------------
# Task Model
# ------------------
class Task(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Task belongs to a user
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='none', blank=True)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField()
    reminder = models.CharField(max_length=10, choices=REMINDER_CHOICES, default='none', blank=True)
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} ({self.user.username})"

# Plan your tasks model used to plan tasks for a day
class PlanYourTasks(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    preferred_start_time = models.TimeField()
    preferred_end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')  # one plan per user per day

    def __str__(self):
        return f"{self.user.username} plan for {self.date}"

# ScheduledTask saves the intermediary task suggestions
class ScheduledTask(models.Model):
    plan = models.ForeignKey('PlanYourTasks', on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='none', blank=True)
    duration = models.DurationField(null=True, blank=True)  # hours + minutes for scheduling
    start_time = models.TimeField(null=True, blank=True)    # set by scheduler
    end_time = models.TimeField(null=True, blank=True)      # set by scheduler
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.plan.user.username} on {self.plan.date})"