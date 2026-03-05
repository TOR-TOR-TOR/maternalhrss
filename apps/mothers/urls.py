# apps/mothers/urls.py
from django.urls import path
from . import views

app_name = 'mothers'

urlpatterns = [
    # Mothers
    path('',                                        views.mother_list_view,       name='list'),
    path('register/',                               views.mother_register_view,   name='register'),
    path('<int:pk>/',                               views.mother_detail_view,     name='detail'),
    path('<int:pk>/edit/',                          views.mother_update_view,     name='update'),

    # Pregnancies
    path('<int:mother_pk>/pregnancy/register/',     views.pregnancy_register_view, name='register_pregnancy'),
    path('pregnancy/<int:pk>/',                     views.pregnancy_detail_view,   name='pregnancy_detail'),
    path('pregnancy/<int:pk>/edit/',                views.pregnancy_update_view,   name='pregnancy_update'),
]