from django.http import HttpResponse
from django.shortcuts import render


def home(request):
    # renders homepage
    return render(request, "base.html")