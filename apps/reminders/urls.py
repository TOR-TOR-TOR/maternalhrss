# apps/reminders/urls.py
from django.urls import path
from . import views

app_name = 'reminders'

urlpatterns = [
    # SMS Log
    path('',                                        views.reminder_list_view,           name='list'),
    path('<int:pk>/',                               views.reminder_detail_view,         name='detail'),

    # Manual Triggers
    path('send/anc/<int:anc_visit_pk>/',            views.send_anc_reminder_view,       name='send_anc'),
    path('send/vaccine/<int:immunization_pk>/',     views.send_vaccine_reminder_view,   name='send_vaccine'),
    path('send/delivery/<int:pregnancy_pk>/',       views.send_delivery_reminder_view,  name='send_delivery'),

    # Template Management (Manager/MOH)
    path('templates/',                              views.template_list_view,           name='template_list'),
    path('templates/<int:pk>/',                     views.template_detail_view,         name='template_detail'),
]