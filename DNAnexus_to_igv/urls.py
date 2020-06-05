from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.nexus_search, name='nexus_search'),
]