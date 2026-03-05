# apps/anc/urls.py
from django.urls import path
from . import views

app_name = 'anc'

urlpatterns = [
    path('',                views.anc_list_view,   name='list'),
    path('<int:pk>/',       views.anc_detail_view, name='detail'),
    path('<int:pk>/record/',views.anc_record_view, name='record_visit'),
    path('<int:pk>/edit/',  views.anc_update_view, name='update'),
]