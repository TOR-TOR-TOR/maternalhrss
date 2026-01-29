# apps/mothers/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Mother, Pregnancy


@admin.register(Mother)
class MotherAdmin(admin.ModelAdmin):
    """
    Admin interface for managing mothers
    Displays key information and allows filtering/searching
    """
    
    list_display = [
        'full_name',
        'age',
        'phone_number',
        'facility',
        'county',
        'has_active_pregnancy',
        'total_pregnancies',
        'registration_date',
        'is_active'
    ]
    
    list_filter = [
        'facility',
        'county',
        'sub_county',
        'is_active',
        'registration_date',
    ]
    
    search_fields = [
        'first_name',
        'last_name',
        'phone_number',
        'national_id',
        'county',
        'sub_county',
        'ward',
        'village'
    ]
    
    readonly_fields = [
        'registration_date',
        'created_at',
        'updated_at',
        'age',
        'total_pregnancies',
        'active_pregnancy'
    ]
    
    date_hierarchy = 'registration_date'
    
    ordering = ['-registration_date']
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'first_name',
                'last_name',
                'date_of_birth',
                'age',
                'national_id'
            )
        }),
        ('Contact Information', {
            'fields': (
                'phone_number',
                'alternate_phone'
            )
        }),
        ('Location Details', {
            'fields': (
                'county',
                'sub_county',
                'ward',
                'village'
            )
        }),
        ('Emergency Contact', {
            'fields': (
                'next_of_kin_name',
                'next_of_kin_phone',
                'next_of_kin_relationship'
            ),
            'classes': ('collapse',)
        }),
        ('Facility & Registration', {
            'fields': (
                'facility',
                'registered_by',
                'registration_date'
            )
        }),
        ('Pregnancy Status', {
            'fields': (
                'total_pregnancies',
                'active_pregnancy'
            ),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        """Display full name"""
        return obj.full_name
    full_name.short_description = 'Mother Name'
    
    def has_active_pregnancy(self, obj):
        """Display active pregnancy status with color"""
        if obj.has_active_pregnancy:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Active</span>'
            )
        return format_html(
            '<span style="color: gray;">No</span>'
        )
    has_active_pregnancy.short_description = 'Active Pregnancy'
    
    def get_queryset(self, request):
        """Optimize queries by selecting related objects"""
        qs = super().get_queryset(request)
        return qs.select_related('facility', 'registered_by').prefetch_related('pregnancies')


@admin.register(Pregnancy)
class PregnancyAdmin(admin.ModelAdmin):
    """
    Admin interface for managing pregnancies
    Highlights auto-calculated fields and risk levels
    """
    
    list_display = [
        'mother_name',
        'gravida_para',
        'gestational_age',
        'edd_display',
        'time_to_delivery',
        'risk_level_display',
        'status',
        'facility',
        'registration_date'
    ]
    
    list_filter = [
        'status',
        'risk_level',
        'facility',
        'registration_date',
        'edd',
    ]
    
    search_fields = [
        'mother__first_name',
        'mother__last_name',
        'mother__phone_number',
    ]
    
    readonly_fields = [
        'edd',
        'gestational_age_weeks',
        'registration_date',
        'created_at',
        'updated_at',
        'weeks_remaining',
        'days_remaining',
        'trimester',
        'is_overdue'
    ]
    
    date_hierarchy = 'edd'
    
    ordering = ['-registration_date']
    
    fieldsets = (
        ('Mother Information', {
            'fields': ('mother',)
        }),
        ('Pregnancy Details', {
            'fields': (
                'pregnancy_number',
                'parity',
                'lmp',
            ),
            'description': 'Enter LMP (Last Menstrual Period) - EDD will be calculated automatically'
        }),
        ('AUTO-CALCULATED DATES', {
            'fields': (
                'edd',
                'gestational_age_weeks',
                'weeks_remaining',
                'days_remaining',
                'trimester',
                'is_overdue'
            ),
            'classes': ('collapse',),
            'description': 'These fields are automatically calculated from LMP'
        }),
        ('Risk Assessment', {
            'fields': (
                'risk_level',
                'risk_factors'
            )
        }),
        ('Obstetric History', {
            'fields': (
                'previous_csection',
                'previous_complications'
            ),
            'classes': ('collapse',)
        }),
        ('Status & Facility', {
            'fields': (
                'status',
                'facility',
                'registered_by',
                'registration_date'
            )
        }),
        ('Additional Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        }),
    )
    
    def mother_name(self, obj):
        """Display mother's name"""
        return obj.mother.full_name
    mother_name.short_description = 'Mother'
    
    def gravida_para(self, obj):
        """Display G/P notation"""
        return obj.gravida_para_display
    gravida_para.short_description = 'G/P'
    
    def gestational_age(self, obj):
        """Display current gestational age"""
        return f"{obj.gestational_age_weeks} weeks (Trimester {obj.trimester})"
    gestational_age.short_description = 'Gestational Age'
    
    def edd_display(self, obj):
        """Display EDD with auto-calculated indicator"""
        return format_html(
            '{} <span style="color: blue; font-size: 0.9em;">(auto-calculated)</span>',
            obj.edd.strftime('%d %b %Y')
        )
    edd_display.short_description = 'EDD'
    
    def time_to_delivery(self, obj):
        """Display time remaining with color coding"""
        if obj.status != 'ACTIVE':
            return obj.get_status_display()
        
        if obj.is_overdue:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ {}</span>',
                obj.get_time_to_delivery_display()
            )
        elif obj.weeks_remaining <= 2:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{}</span>',
                obj.get_time_to_delivery_display()
            )
        else:
            return obj.get_time_to_delivery_display()
    time_to_delivery.short_description = 'Time to Delivery'
    
    def risk_level_display(self, obj):
        """Display risk level with color coding"""
        colors = {
            'LOW': 'green',
            'MEDIUM': 'orange',
            'HIGH': 'red'
        }
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(obj.risk_level, 'black'),
            obj.get_risk_level_display()
        )
    risk_level_display.short_description = 'Risk Level'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('mother', 'facility', 'registered_by')
    
    def save_model(self, request, obj, form, change):
        """
        Override to show message about auto-calculation
        """
        super().save_model(request, obj, form, change)
        
        if not change:  # New pregnancy
            self.message_user(
                request,
                f"✓ Pregnancy registered! EDD auto-calculated: {obj.edd.strftime('%d %b %Y')} "
                f"(Current: {obj.gestational_age_weeks} weeks)"
            )


# Custom admin site configuration
admin.site.site_header = "Maternal Health System Administration"
admin.site.site_title = "Maternal Health Admin"
admin.site.index_title = "Welcome to Maternal Health System"