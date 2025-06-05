from django.db import models

class Post(models.model):
    title = models.CharField(max_length=100)
    content = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)


def __str__(self):
    return self.title