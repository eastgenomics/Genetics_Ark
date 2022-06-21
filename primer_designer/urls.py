from django.urls import path, re_path
from . import views

urlpatterns = [
    # Default view if the user have not navigated yet
    path('primer_designer', views.index, name='primers_index'),
    re_path('create', views.create, name='primers_create'),
]
