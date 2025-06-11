from django.db import models
class flight(models.Model):
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    duration = models.IntegerField()
# Create your models here.
