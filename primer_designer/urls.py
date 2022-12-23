from django.urls import path, re_path
from . import views


app_name = 'primer_designer'

urlpatterns = [
    path('', views.index, name='index'),
    path('task/<str:task_id>', views.task)
]
