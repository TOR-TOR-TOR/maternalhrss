from django.contrib import admin
from django.utils.html import format_html
from datetime import date
from .models import VaccineType, ImmunizationSchedule

@admin.register(VaccineType)
class VaccineTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'age_display', 'route', 'dosage', 'is_active']
    list_filter = ['is_active', 'recommended_age_weeks']
    search_fields = ['name', 'description']
    ordering = ['recommended_age_weeks', 'name']


@admin.register(ImmunizationSchedule)
class ImmunizationScheduleAdmin(admin.ModelAdmin):
    list_display = [
        'baby_name',
        'vaccine_name',
        'scheduled_date_display',
        'baby_age_at_schedule',
        'status_display',
        'administration_date',   # ← FIXED
        'facility',
    ]
    
    list_filter = [
        'administered',
        'missed',
        'vaccine',
        'facility',
        'scheduled_date',
    ]
    
    search_fields = [
        'baby__first_name',
        'baby__mother__first_name',
        'baby__mother__last_name',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Baby & Vaccine', {
            'fields': ('baby', 'vaccine')
        }),
        ('Schedule', {
            'fields': ('scheduled_date',)
        }),
        ('Administration', {
            'fields': (
                'administered',
                'administration_date',
                'batch_number',
                'expiry_date',
                'administered_by',
            )
        }),
        ('Status', {
            'fields': ('missed',)
        }),
        ('Adverse Events', {
            'fields': (
                'adverse_event',
                'adverse_event_details',
            ),
            'classes': ('collapse',)
        }),
        ('Facility & Notes', {
            'fields': (
                'facility',
                'notes',
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    # Disable manual creation - vaccines auto-generate when baby is born
    def has_add_permission(self, request):
        """Only Managers and MOH can manually add vaccines"""
        if request.user.is_superuser:
            return True
        return request.user.role in ['MANAGER', 'MOH']
    
    def baby_name(self, obj):
        return obj.baby.display_name
    baby_name.short_description = 'Baby'
    
    def vaccine_name(self, obj):
        return obj.vaccine.name
    vaccine_name.short_description = 'Vaccine'
    
    def scheduled_date_display(self, obj):
        if not obj.scheduled_date:
            return '-'
        
        today = date.today()
        
        if obj.administered:
            return format_html(
                '<span style="color: green;">{}</span>',
                obj.scheduled_date.strftime('%d %b %Y')
            )
        elif obj.missed:
            return format_html(
                '<span style="color: red; font-weight: bold;">{}</span>',
                obj.scheduled_date.strftime('%d %b %Y')
            )
        elif obj.scheduled_date < today:
            return format_html(
                '<span style="color: orange; font-weight: bold;">{} (OVERDUE)</span>',
                obj.scheduled_date.strftime('%d %b %Y')
            )
        elif obj.scheduled_date == today:
            return format_html(
                '<span style="color: blue; font-weight: bold;">{} (TODAY)</span>',
                obj.scheduled_date.strftime('%d %b %Y')
            )
        else:
            return obj.scheduled_date.strftime('%d %b %Y')
    scheduled_date_display.short_description = 'Scheduled Date'
    
    def status_display(self, obj):
        status_config = {
            'Administered': ('✓', 'green', 'bold'),
            'Missed': ('✗', 'red', 'bold'),
            'Overdue': ('⚠', 'orange', 'bold'),
            'Due Today': ('●', 'blue', 'bold'),
            'Upcoming': ('○', 'gray', 'normal'),
        }
        
        icon, color, weight = status_config.get(obj.status, ('?', 'black', 'normal'))
        
        return format_html(
            '<span style="color: {}; font-weight: {};">{} {}</span>',
            color, weight, icon, obj.status
        )
    status_display.short_description = 'Status'
    
    def admin_date_display(self, obj):
        """Display when vaccine was administered"""
        if obj.administration_date:
            return obj.administration_date.strftime('%d %b %Y')
        return '-'
    admin_date_display.short_description = 'Given On'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('baby__mother', 'vaccine', 'facility')