from django.http import HttpResponse
from django.shortcuts import render
from django.contrib import messages



def home(request):
    # renders homepage
    return render(request, "genetics_ark/genetics_ark.html")