from django.urls import path
from . import views

app_name = 'DNAnexus_to_igv'
urlpatterns = [
    path('nexus_search', views.nexus_search, name='nexus_search'),
]
