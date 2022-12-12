from django.shortcuts import render
from ga_core.settings import GRID_SERVICE_DESK, GRID_IVA


# @login_required
def home(request):
    context_dict = {}
    context_dict['desk'] = GRID_SERVICE_DESK
    context_dict['iva'] = GRID_IVA

    # renders homepage
    return render(request, "genetics_ark/genetics_ark.html", context_dict)


def error404(request, exception):
    return render(request, '404.html', status=404)


def error500(request):
    return render(request, '500.html', status=500)


def error502(request, exception):
    return render(request, '502.html', status=502)
