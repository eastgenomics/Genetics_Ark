from django.urls import path
from . import views

app_name = "primer"

urlpatterns = [
    path("", views.index, name="index"),
    path("task/<str:task_id>", views.task, name="task"),
]
