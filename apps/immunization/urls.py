# apps/immunization/urls.py
from django.urls import path
from . import views

app_name = 'immunization'

urlpatterns = [
    path('',                    views.immunization_list_view,   name='list'),
    path('<int:pk>/',           views.immunization_detail_view, name='detail'),
    path('<int:pk>/record/',    views.immunization_record_view, name='record'),
    path('<int:pk>/edit/',      views.immunization_update_view, name='update'),
]