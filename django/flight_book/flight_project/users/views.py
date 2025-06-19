from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.urls import reverse


def index(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('login'))
    return render(request, "users/user.html")

def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "users/login.html", {
                "message": "Invalid credentials."
            })
    return render(request, "users/login.html")

def logout_view(request):
    logout(request)
    return render(request, "users/login.html",
        {"message": "You have been logged out."}
    )




def register_view(request):
    if request.method == "POST":
        errors = {}
        username = request.POST.get("username")
        firstname = request.POST.get("first_name")
        lastname = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirmation = request.POST.get("confirmation")

        if not lastname:
            errors['lastname'] = "Username cannot be empty."
        elif User.objects.filter(last_name=lastname).exists():
            errors['lastname'] = "Username already taken."
        if not firstname:
            errors['firstname'] = "Firstname cannot be empty."
        elif User.objects.filter(first_name=firstname).exists():
            errors['firstname'] = "Firstname already taken."
        if not username:
            errors['username'] = "Username cannot be empty."
        elif User.objects.filter(username=username).exists():
            errors['username'] = "Username already taken."

        if not email:
            errors['email'] = "Email cannot be empty."
        elif User.objects.filter(email=email).exists():
            errors['email'] = "Email already registered."

        if not password:
            errors['password'] = "Password cannot be empty."
        elif len(password) < 8:
            errors['password'] = "Password must be at least 8 characters long."

        if not confirmation:
            errors['confirmation'] = "Confirm password cannot be empty."
        elif password != confirmation:
            errors['confirmation'] = "Passwords do not match."

        # --- Corrected logic for handling errors and success ---
        if not errors:  # If no errors were found, proceed with user creation
            try:
                user = User.objects.create_user(username=username, email=email, password=password,first_name=firstname,last_name=lastname)
                login(request, user)
                messages.success(request, f"Welcome, {username}! You have been registered.")
                return HttpResponseRedirect(reverse("index"))
            except Exception as e:
                # This catch block is for unexpected server-side errors, not client-side validation
                messages.error(request, f"An unexpected error occurred during registration: {e}")
                return render(request, "users/register.html", {
                    "username": username,
                    "email": email,
                    "errors": errors, # Pass existing data and errors back
                    "message": "Registration failed due to an internal error."
                })
        else:
            # If there are errors, re-render the form with error messages
            return render(request, "users/register.html", {
                "username": username,
                "email": email,
                "errors": errors,
                "message": "Please correct the errors below."
            })

    else:
        # Handle GET requests: render the empty form
        return render(request, "users/register.html")




