"""ga_core URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from ga_core.settings import LOCAL_WORKSTATION

from genetics_ark.views import error404, error500, error502

handler404 = error404
handler500 = error500
handler502 = error502

urlpatterns = (
    [
        path("genetics_ark/", include("genetics_ark.urls")),
        path("genetics_ark/accounts/", include("accounts.urls")),
        path("genetics_ark/admin/", admin.site.urls),
        path("genetics_ark/igv/", include("DNAnexus_to_igv.urls"), name="igv"),
        path(
            "genetics_ark/primer_designer/",
            include("primer_designer.urls"),
            name="primer",
        ),
    ]
    if not LOCAL_WORKSTATION
    else [
        path("", include("genetics_ark.urls")),
        path("accounts/", include("accounts.urls")),
        path("admin/", admin.site.urls),
        path("igv/", include("DNAnexus_to_igv.urls"), name="igv"),
        path(
            "primer_designer/", include("primer_designer.urls"), name="primer"
        ),
    ]
)
