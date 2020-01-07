from django.conf.urls import url, include
from django.views.generic import RedirectView
from . import views
from django.views.generic import TemplateView


urlpatterns = [
               # Default view if the user has not navigated yet
               url(r'^$', views.index, name='primer_db_index'),

               url(r'^help/$', TemplateView.as_view(template_name='primer_db/help.html'), name='help_page'),           

               url(r'^submit/$', views.submit, name = 'submit'),

               url(r'^submit_pair/$', views.submit_pair, name = 'submit_pair'),

               url(r'^edit_primer/(?P<PrimerDetails_id>[0-9]+)/$', views.edit_primer, name = 'edit_primer'),

               url(r'^edit_pair/(?P<PrimerDetails_id>[0-9]+)/$', views.edit_pair, name = 'edit_pair')

               ]

