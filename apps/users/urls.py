# apps/users/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Password Management
    path('password/change/', views.change_password, name='change_password'),
    path('password/reset/', views.password_reset_request, name='password_reset'),
    
    # Dashboard (redirects to role-specific dashboard)
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Role-specific dashboards (placeholders)
    path('dashboard/nurse/', views.nurse_dashboard, name='nurse_dashboard'),
    path('dashboard/manager/', views.manager_dashboard, name='manager_dashboard'),
    path('dashboard/moh/', views.moh_dashboard, name='moh_dashboard'),
]


