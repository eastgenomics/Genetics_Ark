from django.shortcuts import render
from django.contrib.auth.decorators import login_required


# @login_required
def home(request):
    # renders homepage
    return render(request, "genetics_ark/genetics_ark.html")


def error404(request, exception):
    return render(request, '404.html', status=404)


def error500(request):
    return render(request, '500.html', status=500)


def error502(request, exception):
    return render(request, '502.html', status=502)
