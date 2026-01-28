# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Facility


@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    """Admin interface for managing health facilities"""
    
    list_display = [
        'name',
        'facility_level',
        'county',
        'sub_county',
        'phone_number',
        'has_maternity_services',
        'is_24_hours',
        'is_active'
    ]
    
    list_filter = [
        'facility_level',
        'county',
        'is_active',
        'has_maternity_services',
        'is_24_hours',
    ]
    
    search_fields = [
        'name',
        'county',
        'sub_county',
        'ward',
        'mfl_code',
        'phone_number'
    ]
    
    ordering = ['county', 'facility_level', 'name']
    
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'facility_level', 'mfl_code')
        }),
        ('Location Details', {
            'fields': ('county', 'sub_county', 'ward', 'village')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'alternate_phone', 'email')
        }),
        ('Services & Operations', {
            'fields': (
                'has_maternity_services',
                'is_24_hours',
                'is_active'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Show number of staff members
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related('staff')


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin interface for managing system users"""
    
    list_display = [
        'username',
        'first_name',
        'last_name',
        'role',
        'facility',
        'phone_number',
        'is_active',
        'is_staff'
    ]
    
    list_filter = [
        'role',
        'facility',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined'
    ]
    
    search_fields = [
        'username',
        'first_name',
        'last_name',
        'phone_number',
        'email'
    ]
    
    ordering = ['-date_joined']
    
    readonly_fields = ['date_joined', 'last_login', 'created_at', 'updated_at']
    
    # Fieldsets for EDITING existing users
    fieldsets = (
        ('Login Credentials', {
            'fields': ('username', 'password')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Role & Assignment', {
            'fields': ('role', 'phone_number', 'facility'),
            'description': 'MOH Administrators do not need facility assignment'
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'is_active_user',
                'groups',
                'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Fieldsets for ADDING new users
    add_fieldsets = (
        ('Login Credentials', {
            'fields': ('username', 'password1', 'password2')
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'email')
        }),
        ('Role & Assignment', {
            'fields': ('role', 'phone_number', 'facility'),
            'description': 'All fields are required. MOH admins can leave facility blank.'
        }),
        ('Permissions (Optional)', {
            'fields': ('is_staff', 'is_superuser'),
            'classes': ('collapse',)
        }),
    )
    
    # Enable filtering by facility
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('facility')
    
    # Custom display for facility
    def facility(self, obj):
        return obj.get_facility_name()
    facility.short_description = 'Assigned Facility'