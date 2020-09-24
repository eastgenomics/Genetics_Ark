from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required


@login_required
def home(request):
    # renders homepage
    return render(request, "genetics_ark/genetics_ark.html")