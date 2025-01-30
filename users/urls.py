from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.criar_usuario),
    path('login/', views.login),
]
