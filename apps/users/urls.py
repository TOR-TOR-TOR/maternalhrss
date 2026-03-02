# apps/users/urls.py
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [

    # ── Auth ──────────────────────────────────────────
    path('auth/login/',  views.LoginView.as_view(), name='login'),
    path('auth/logout/', views.logout_view,          name='logout'),

    # ── Users ─────────────────────────────────────────
    path('users/',                  views.user_list_view,   name='user_list'),
    path('users/register/',         views.register_view,    name='register'),
    path('users/profile/',          views.profile_view,     name='profile'),
    path('users/<int:pk>/',         views.user_detail_view, name='user_detail'),
    path('users/<int:pk>/edit/',    views.user_update_view, name='user_update'),

    # ── Facilities ────────────────────────────────────
    path('facilities/',                  views.facility_list_view,   name='facility_list'),
    path('facilities/create/',           views.facility_create_view, name='facility_create'),
    path('facilities/<int:pk>/',         views.facility_detail_view, name='facility_detail'),
    path('facilities/<int:pk>/edit/',    views.facility_update_view, name='facility_update'),

]