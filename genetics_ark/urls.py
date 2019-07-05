from django.conf.urls import  url
from genetics_ark import views

urlpatterns = [
    # Default view if the user have not navigated yet
    url(r'^$', views.index, name='index'),
    
    url(r'^variant/(?P<chrom>[0-9XYxy]+)/(?P<pos>[0-9]+)/$', views.variant_view, name='variant_view'),
    url(r'^variant/(?P<chrom>[0-9XYxy]+)/(?P<pos>[0-9]+)/(?P<ref>[ACGT]+)/(?P<alt>[ACGT]+)/$', views.variant_view, name='variant_view'),
        
    url(r'^projects/$', views.projects_list, name='projects_list'),

    url(r'^igv/(?P<analysis_id>[0-9]+)/$', views.igv, name='igv'),
    url(r'^igv/(?P<sample_name>[GXWIC0-9]+)/(?P<runfolder_name>[KNM\_0-9]+)/$', views.igv, name='igv'),
    url(r'^igv/(?P<sample_name>[GXWIC0-9]+)/(?P<runfolder_name>[KNM\_0-9]+)/(?P<chrom>[0-9XYxy]+)/(?P<pos>[0-9]+)/$', views.igv, name='igv'),
    url(r'^igv/(?P<analysis_id>[0-9]+)/(?P<chrom>[0-9XYxy]+)/(?P<pos>[0-9]+)/$', views.igv, name='igv'),
    
    url(r'^sample/(?P<sample_id>[0-9]+)/$', views.sample_view, name='sample_view'),
    url(r'^sample/(?P<sample_name>[A-Z0-9]+)/$', views.sample_view, name='sample_view'),

    url(r'^analysis/report/(?P<analysis_id>[0-9]+)/$', views.analysis_report, name='analysis_report'),

    url(r'^analysis/report/create/(?P<analysis_id>[0-9]+)/$', views.report_create, name='report_create'),
    url(r'^analysis/report/create/(?P<analysis_id>[0-9]+)/$', views.report_create, name='report_create'),
    url(r'^analysis/report/done/(?P<tmp_key>[0-9a-zA-Z]+)/$', views.report_done_ajax, name='report_done_ajax'),

    url(r'^panel/(?P<panel_id>[0-9]+)/$', views.panel_view, name='panel_view'),
    url(r'^gene/(?P<gene_name>[A-Za-z0-9\-]+)/$', views.gene_view, name='gene_view'),
    
    url(r'^qc/project/(?P<project_id>[0-9]+)/$', views.qc_project, name='qc_project'),
    url(r'^qc/runfolder/(?P<runfolder_id>[0-9]+)/$', views.qc_runfolder, name='qc_runfolder'),
    
    url(r'^docs/notes/$', views.doc_notes, name='doc_notes'),
    
    url(r'^api/search/(?P<query>[a-zA-Z0-9\-\_:]+)/$', views.api_search, name='api_search'),
    url(r'^search/$', views.search, name='search'),
    
    url(r'^cnv/(?P<CNV_id>[0-9]+)/$', views.cnv_view, name='cnv_view'),

    url(r'^decon/(?P<Decon_id>[0-9]+)/$', views.decon_view, name='decon_view'),

    url(r'^deconexon/(?P<Deconexon_id>[0-9]+)/$', views.deconexon_view, name='deconexon_view'),
    url(r'^decongene/decongene-(?P<parameter>[\w]+).html', views.decongene_view, name='decongene_view')
]
