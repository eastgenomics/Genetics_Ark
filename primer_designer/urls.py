from django.conf.urls import url
from primer_designer import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = [
               # Default view if the user have not navigated yet
               url(r'^$', views.index, name='primers_index'),
               
               url(r'^create/$', views.create, name='primers_create'),
               url(r'^primers_done_ajax/(?P<tmp_key>[0-9a-zA-Z]+)$', views.primers_done_ajax, name='primers_done_ajax'),
               url(r'^position/$', views.render_position, name="position"),
               url(r'^range/$', views.render_range, name='range'),
               url(r'^fusion/$', views.render_fusion, name='fusion')
]


# if settings.DEBUG:
#     urlpatterns += staticfiles_urlpatterns()