from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Redirect root URL to login
    path('', lambda request: redirect('login'), name='home'),
    
    # Authentication & User Management
    path('users/', include('apps.users.urls')),
]

# Customize admin site headers
admin.site.site_header = "Maternal Health System Admin"
admin.site.site_title = "Maternal Health Admin"
admin.site.index_title = "System Administration"