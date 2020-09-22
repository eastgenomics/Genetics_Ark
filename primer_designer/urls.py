from django.conf.urls import url
from django.urls import include, path
from . import views

urlpatterns = [
    # Default view if the user have not navigated yet
    path('primer_designer', views.index, name='primers_index'),
    # url(r'^$', views.index, name='primers_index'),
    url(r'^create/$', views.create, name='primers_create'),
    url(r'^primers_done_ajax/(?P<tmp_key>[0-9a-zA-Z]+)$', views.primers_done_ajax, name='primers_done_ajax'),   
]
