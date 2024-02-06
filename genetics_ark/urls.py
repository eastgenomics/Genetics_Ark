from django.urls import path

from . import views

app_name = "genetics"

urlpatterns = [
    path("", views.home, name="index"),
]
