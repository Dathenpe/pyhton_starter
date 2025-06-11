from django import forms
from .models import Post, Account


class  PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']


class AccountForm(forms.ModelForm):
        class Meta:
            model = Account
            fields = ['username', 'password','email','phone']