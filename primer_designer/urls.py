from django.urls import path, re_path
from . import views


app_name = 'primer_designer'

urlpatterns = [
    # Default view if the user have not navigated yet
    path('', views.index, name='index'),
]
