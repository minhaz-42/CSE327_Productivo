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
