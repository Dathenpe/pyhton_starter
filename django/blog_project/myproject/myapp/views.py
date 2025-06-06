from django.shortcuts import render, redirect

from .form import PostForm
from .models import Post


def home(request):
    posts =Post.objects.all()
    return render(request, 'home.html', {'posts': posts})

def create_post(request):
    if request.method == 'POST':
       form = PostForm(request.POST)
       if form.is_valid():
           form.save()
       else:
           form = PostForm()
    return render(request, 'create_post.html', {'form': form})

# Create your views here.
