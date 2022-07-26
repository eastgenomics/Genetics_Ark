from django.urls import path
from . import views

app_name = 'igv'

urlpatterns = [
    path('', views.nexus_search, name='nexus_search'),
]
