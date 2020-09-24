from django.conf.urls import url
from django.urls import include, path
from . import views

urlpatterns = [
    # Default view if the user have not navigated yet
    path('primer_designer', views.index, name='primers_index'),
    url(r'^create/$', views.create, name='primers_create'),
]
