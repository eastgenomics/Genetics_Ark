from django.conf.urls import  url
from genetics_ark import views

urlpatterns = [
                       # Default view if the user have not navigated yet
                       url(r'^$', views.index, name='index'),


#                       url(r'^region/$', views.region, name='freq_index'),
                       url(r'^variant/(?P<chrom>[0-9XYxy]+)/(?P<pos>[0-9]+)/$', views.variant_view, name='variant_view'),
                       url(r'^variant/(?P<chrom>[0-9XYxy]+)/(?P<pos>[0-9]+)/(?P<ref>[ACGT]+)/(?P<alt>[ACGT]+)/$', views.variant_view, name='variant_view'),


                       url(r'^projects/$', views.projects_list, name='projects_list'),

                       url(r'^sample/(?P<sample_id>[0-9]+)/$', views.sample_view, name='sample_view'),
                       url(r'^sample/(?P<sample_name>[A-Z0-9]+)/$', views.sample_view, name='sample_view'),


                       url(r'^panel/(?P<panel_id>[0-9]+)/$', views.panel_view, name='panel_view'),
                       url(r'^gene/(?P<gene_name>[A-Za-z0-9\-]+)/$', views.gene_view, name='gene_view'),

                       url(r'^qc/project/(?P<project_id>[0-9]+)/$', views.qc_project, name='qc_project'),
                       url(r'^qc/runfolder/(?P<runfolder_id>[0-9]+)/$', views.qc_runfolder, name='qc_runfolder'),
#                       url(r'^qc/sample/(?P<sample_id>[0-9]+)/$', views.qc_sample, name='qc_sample'),


                       
                       url(r'^docs/notes/$', views.doc_notes, name='doc_notes'),

                       
                       url(r'^api/search/(?P<query>[a-zA-Z0-9\-\_:]+)/$', views.api_search, name='api_search'),
                       url(r'^search/$', views.search, name='search'),


                       ]
