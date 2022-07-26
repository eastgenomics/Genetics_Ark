from django.urls import path
from . import views

app_name = 'igv'

urlpatterns = [
    path('', views.index, name='index'),
    path('search', views.search, name='search'),
    path('select', views.select, name='select'),
    path('view', views.view, name='view'),
    path('link', views.link, name='link')
]
