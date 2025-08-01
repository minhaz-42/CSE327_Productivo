from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Student(models.Model):
   user = models.OneToOneField(User, on_delete= models.CASCADE)   ##each student linked to a user
   dob = models.DateField()
   institution = models.CharField(max_length=255)
   profile_pic = models.ImageField(upload_to= 'profile_pics/', blank = True, null = True)

   def __str__(self):
      return self.user.username
# Task Model

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    REMINDER_CHOICES = [
        ('none', 'None'),
        ('10min', '10 minutes before'),
        ('15min', '15 minutes before'),
        ('1hr', '1 hour before'),
        ('1day', '1 day before'),
    ]
    
    CATEGORY_CHOICES = [
        ('none', 'None'),
        ('work', 'Work'),
        ('personal', 'Personal'),
        ('finance', 'Finance'),
         ('health', 'Health'),
         ('study', 'Study'),
         ('other', 'Other'),
        # Add more as needed
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)  # Task belongs to a user
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='none', blank=True)
    deadline = models.DateTimeField()
    reminder = models.CharField(max_length=10, choices=REMINDER_CHOICES, default='none', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} ({self.user.username})"