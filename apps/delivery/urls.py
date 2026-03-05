# apps/delivery/urls.py
from django.urls import path
from . import views

app_name = 'delivery'

urlpatterns = [
    # Deliveries
    path('',                                        views.delivery_list_view,   name='list'),
    path('<int:pk>/',                               views.delivery_detail_view, name='detail'),
    path('record/<int:pregnancy_pk>/',              views.delivery_create_view, name='record'),

    # Babies
    path('<int:delivery_pk>/register-baby/',        views.baby_register_view,   name='register_baby'),
    path('baby/<int:pk>/',                          views.baby_detail_view,     name='baby_detail'),
]