from django.urls import path

from . import views

urlpatterns = [
    path('login/', views.index, name="login"),
    path('accounts/sign_up/', views.sign_up, name="sign-up"),
    path('accounts/log_out/', views.log_out, name="log_out"),
    path('activate/<slug:uid>/<slug:token>/', views.activate, name='activate')
]
