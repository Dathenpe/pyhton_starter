from django.shortcuts import render, redirect
from .form import PostForm, AccountForm
from .models import Post, Account


def home(request):
    posts = Post.objects.all()
    accounts = Account.objects.all()
    return render(request, 'home.html', {'posts': posts, 'accounts': accounts})

def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = PostForm()
    return render(request, 'create_post.html', {'form': form})

def create_account(request):
    if request.method == 'POST':
        form = AccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        form = AccountForm()
    return render(request, 'create_account.html', {'form': form})