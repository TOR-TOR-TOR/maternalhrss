# apps/mothers/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.mother_list, name='mother_list'),
    path('create/', views.mother_create, name='mother_create'),
    path('<int:pk>/', views.mother_detail, name='mother_detail'),
    path('<int:pk>/edit/', views.mother_edit, name='mother_edit'),
    path('<int:pk>/delete/', views.mother_delete, name='mother_delete'),
]