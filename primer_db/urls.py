from django.conf.urls import url, include
from . import views



urlpatterns = [
               # Default view if the user have not navigated yet
               url(r'^$', views.index, name='primer_db_index'),

               url(r'^search/$', views.search, name = 'search_results'),

              
               url(r'^edit_primer/(?P<PrimerDetails_id>[0-9]+)/$', views.edit_primer, name = 'edit_primer')

               # url(r'^edit_primer/$', views.edit_primer, name = 'edit_primers')

               ]


