# apps/anc/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.anc_visit_list, name='anc_visit_list'),
    path('record/<int:visit_id>/', views.anc_visit_record, name='anc_visit_record'),
    path('create/', views.anc_visit_create, name='anc_visit_create'),
    path('<int:pk>/', views.anc_visit_detail, name='anc_visit_detail'),
    path('<int:pk>/edit/', views.anc_visit_edit, name='anc_visit_edit'),
]