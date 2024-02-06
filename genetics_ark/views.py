from django.shortcuts import render
from ga_core.settings import GRID_SERVICE_DESK


def home(request):
    # renders homepage
    return render(
        request, "genetics_ark/genetics_ark.html", {"desk": GRID_SERVICE_DESK}
    )


def error404(request, exception):
    return render(request, "404.html", status=404)


def error500(request):
    return render(request, "500.html", status=500)


def error502(request, exception):
    return render(request, "502.html", status=502)
