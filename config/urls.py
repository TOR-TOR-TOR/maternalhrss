from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', lambda request: redirect('users:login'), name='home'),
    path('', include('apps.users.urls', namespace='users')),  # no prefix
    path('mothers/', include('apps.mothers.urls')),
    path('anc/', include('apps.anc.urls')),
]

admin.site.site_header = "Maternal Health System Admin"
admin.site.site_title = "Maternal Health Admin"
admin.site.index_title = "System Administration"