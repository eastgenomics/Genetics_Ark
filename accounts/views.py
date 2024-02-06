from django.contrib import messages
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.urls import reverse

from ga_core.settings import GRID_SERVICE_DESK, LOCAL_WORKSTATION

# forms import
from DNAnexus_to_igv.forms import UrlForm, SearchForm

import logging

from .forms import LoginForm

error_log = logging.getLogger("ga_error")


def login_action(request):
    context_dict = {}
    context_dict["login_form"] = LoginForm()
    context_dict["search_form"] = SearchForm()
    context_dict["url_form"] = UrlForm()
    context_dict["desk"] = GRID_SERVICE_DESK

    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            return redirect(reverse("igv:index"), context_dict)
        else:
            context_dict["error"] = True

            messages.add_message(request, messages.ERROR, "Incorrect Login Credential")
            return render(request, "registration/login.html", context_dict)
    else:
        return render(request, "registration/login.html", context_dict)


def logout_action(request):
    logout(request)
    messages.add_message(request, messages.SUCCESS, "Successfully logged out")
    return redirect(reverse("genetics:index"))
