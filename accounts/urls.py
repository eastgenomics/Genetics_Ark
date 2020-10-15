from django.contrib import admin
from django.urls import path, include
from django_email_verification import urls as mail_urls
from .views import sign_up

from . import views

urlpatterns = [
    path('', views.index, name="home"),
    path('accounts/sign_up/', views.sign_up, name="sign-up"),
    path('accounts/log_out/', views.log_out, name="log_out"),
    path('activate/<slug:uid>/<slug:token>/', views.activate, name='activate')
]