
from django.contrib.auth.models import User
# from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect

from .forms import SignUpForm


@login_required
def index(request):
    return render(request,'accounts/index.html')

def log_out(request):
    logout(request)
    messages.add_message(
        request,
        messages.SUCCESS,
        """Successfully logged out"""
    )
    # redirect to home page which goes back to login
    return redirect('/')


def sign_up(request):
    context = {}
    form = SignUpForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            user = form.save()
            login(request,user)
            return render(request,'genetics_ark/genetics_ark.html')
    context['form']=form
    return render(request,'registration/sign_up.html',context)