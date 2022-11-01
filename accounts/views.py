from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import render, redirect

import logging

from .backends import LDAPBackend
from .forms import LoginForm

error_log = logging.getLogger("ga_error")


def login(request):
    print(request)
    if request.method == 'GET':
        form = LoginForm()
        context = {
            'form': form
        }
        return render(request, 'registration/login.html', context)

    elif request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        print(username, password)
        user = LDAPBackend().authenticate(
            request,
            username=username,
            password=password)
        print(user)
        if user is not None:
            print('Found User!')
            login(request, user)
        else:
            print('user not found')
            messages.add_message(
                request,
                messages.ERROR,
                f"Incorrect login credential"
            )
            form = LoginForm()
            context = {
                'form': form
                }
            return render(
                request, 'registration/login.html', context)


def logout(request):
    logout(request)
    messages.add_message(
        request,
        messages.SUCCESS,
        "Successfully logged out"
    )
    # redirect to home page which goes back to login
    return redirect('/')
