from django.conf.urls import url
from . import views

urlpatterns = [
               # Default view if the user have not navigated yet
               url(r'^$', views.index, name='primer_db_index'),


               ]


