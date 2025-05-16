from django.db import models
from django.contrib.auth.models import User

# Owner Model
class Owner(models.Model):
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=100)  # Store hashed password in real-world use
    phone = models.CharField(max_length=15)


# Manager Model
class Manager(models.Model):
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='managers')
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=256)  # Add this!
    phone = models.CharField(max_length=15)
    
    
class Site(models.Model):
    owner = models.ForeignKey(Owner, on_delete=models.CASCADE, related_name='sites')
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    assigned_managers = models.ManyToManyField(Manager, related_name='sites', blank=True)


class SiteImage(models.Model):
    site = models.ForeignKey('Site', on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='site_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class SiteExpense(models.Model):
    site = models.ForeignKey('Site', on_delete=models.CASCADE, related_name='expenses')
    completion_percentage = models.PositiveIntegerField(default=0)  # daily progress %
    material_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)

