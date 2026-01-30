# apps/anc/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Q
from datetime import date, timedelta
from .models import ANCVisit


@admin.register(ANCVisit)
class ANCVisitAdmin(admin.ModelAdmin):
    """
    Admin interface for managing ANC visits
    Shows attendance status, clinical data, and danger signs
    """
    
    list_display = [
        'visit_info',
        'mother_name',
        'scheduled_date_display',
        'status_display',
        'gestational_age',
        'clinical_summary',
        'danger_signs_display',
        'supplements_display',
        'facility',
    ]
    
    list_filter = [
        'attended',
        'missed',
        'has_danger_signs',
        'facility',
        'scheduled_date',
        'visit_number',
    ]
    
    search_fields = [
        'pregnancy__mother__first_name',
        'pregnancy__mother__last_name',
        'pregnancy__mother__phone_number',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'status',
        'is_overdue',
        'days_until_visit',
    ]
    
    date_hierarchy = 'scheduled_date'
    
    ordering = ['-scheduled_date', 'visit_number']
    
    fieldsets = (
        ('Visit Information', {
            'fields': (
                'pregnancy',
                'visit_number',
                'scheduled_date',
                'actual_visit_date',
            )
        }),
        ('Attendance Status', {
            'fields': (
                'attended',
                'missed',
                'status',
                'is_overdue',
                'days_until_visit',
            ),
            'description': 'Visit attendance tracking'
        }),
        ('Clinical Measurements', {
            'fields': (
                'weight_kg',
                'blood_pressure',
                'hemoglobin',
                'fundal_height',
                'fetal_heartbeat',
            ),
            'classes': ('collapse',)
        }),
        ('Danger Signs', {
            'fields': (
                'has_danger_signs',
                'danger_signs_notes',
            ),
            'description': '⚠ Flag any danger signs for immediate attention'
        }),
        ('Interventions & Supplements', {
            'fields': (
                'iron_given',
                'folic_acid_given',
                'deworming_done',
                'tetanus_vaccine_given',
            ),
            'classes': ('collapse',)
        }),
        ('Clinical Notes', {
            'fields': (
                'clinical_notes',
                'next_visit_date',
            ),
            'classes': ('collapse',)
        }),
        ('Facility & Staff', {
            'fields': (
                'facility',
                'recorded_by',
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
    
    # Custom actions
    actions = [
        'mark_as_attended',
        'mark_as_missed',
        'flag_for_followup',
    ]
    
    def visit_info(self, obj):
        """Display visit number with badge - Color coded by trimester"""
        # Trimester-based colors following Kenya 8-contact model
        # T1 (1-12 weeks): Green - Contact 1
        # T2 (13-26 weeks): Blue - Contacts 2-3
        # T3 (27-40 weeks): Orange/Red - Contacts 4-8
        colors = {
            1: '#4CAF50',  # Green - 1st Trimester
            2: '#2196F3',  # Blue - 2nd Trimester
            3: '#2196F3',  # Blue - 2nd Trimester
            4: '#FF9800',  # Orange - 3rd Trimester (early)
            5: '#FF9800',  # Orange - 3rd Trimester
            6: '#FF5722',  # Deep Orange - 3rd Trimester
            7: '#F44336',  # Red - 3rd Trimester (late)
            8: '#D32F2F',  # Dark Red - 3rd Trimester (EDD)
        }
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 4px; font-weight: bold;">ANC {}</span>',
            colors.get(obj.visit_number, '#666'),
            obj.visit_number
        )
    visit_info.short_description = 'Contact'
    
    def mother_name(self, obj):
        """Display mother's name with link to pregnancy"""
        return format_html(
            '<a href="/admin/mothers/pregnancy/{}/change/">{}</a>',
            obj.pregnancy.id,
            obj.pregnancy.mother.full_name
        )
    mother_name.short_description = 'Mother'
    
    def scheduled_date_display(self, obj):
        """Display scheduled date with color coding"""
        if not obj.scheduled_date:
            return '-'
        
        today = date.today()
        
        if obj.attended:
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
        """Display attendance status with icons and colors"""
        status_config = {
            'Attended': ('✓', 'green', 'bold'),
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
    
    def gestational_age(self, obj):
        """Display gestational age at visit"""
        if obj.pregnancy:
            weeks = obj.pregnancy.gestational_age_weeks
            return f"{weeks} weeks"
        return "-"
    gestational_age.short_description = 'GA (weeks)'
    
    def clinical_summary(self, obj):
        """Display summary of clinical measurements"""
        if obj.attended:
            return obj.get_clinical_summary()
        return format_html('<span style="color: gray;">Not recorded</span>')
    clinical_summary.short_description = 'Clinical Data'
    
    def danger_signs_display(self, obj):
        """Display danger signs warning"""
        if obj.has_danger_signs:
            return format_html(
                '<span style="color: red; font-weight: bold;">⚠ YES</span>'
            )
        elif obj.attended:
            return format_html('<span style="color: green;">No</span>')
        return '-'
    danger_signs_display.short_description = 'Danger Signs'
    
    def supplements_display(self, obj):
        """Display supplements given"""
        if obj.attended:
            supplements = obj.get_supplements_given()
            if supplements == "None":
                return format_html('<span style="color: gray;">None</span>')
            return supplements
        return '-'
    supplements_display.short_description = 'Supplements'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'pregnancy__mother',
            'facility',
            'recorded_by'
        ).prefetch_related('pregnancy__mother')
    
    # Custom Admin Actions
    
    def mark_as_attended(self, request, queryset):
        """Mark selected visits as attended"""
        updated = queryset.update(
            attended=True,
            missed=False,
            actual_visit_date=date.today()
        )
        self.message_user(
            request,
            f"{updated} visit(s) marked as attended."
        )
    mark_as_attended.short_description = "Mark selected visits as Attended"
    
    def mark_as_missed(self, request, queryset):
        """Mark selected visits as missed"""
        updated = queryset.update(missed=True)
        self.message_user(
            request,
            f"{updated} visit(s) marked as missed."
        )
    mark_as_missed.short_description = "Mark selected visits as Missed"
    
    def flag_for_followup(self, request, queryset):
        """Flag visits with danger signs for follow-up"""
        updated = queryset.update(has_danger_signs=True)
        self.message_user(
            request,
            f"{updated} visit(s) flagged with danger signs for follow-up.",
            level='WARNING'
        )
    flag_for_followup.short_description = "⚠ Flag for Follow-up (Danger Signs)"
    
    # Custom filters for quick access
    
    def get_list_filter(self, request):
        """Add custom filters"""
        filters = list(self.list_filter)
        
        # Add custom filter classes
        class TodayVisitsFilter(admin.SimpleListFilter):
            title = 'Today\'s Visits'
            parameter_name = 'today'
            
            def lookups(self, request, model_admin):
                return (
                    ('yes', 'Scheduled Today'),
                )
            
            def queryset(self, request, queryset):
                if self.value() == 'yes':
                    return queryset.filter(scheduled_date=date.today())
        
        class OverdueFilter(admin.SimpleListFilter):
            title = 'Overdue Status'
            parameter_name = 'overdue'
            
            def lookups(self, request, model_admin):
                return (
                    ('yes', 'Overdue Visits'),
                )
            
            def queryset(self, request, queryset):
                if self.value() == 'yes':
                    return queryset.filter(
                        scheduled_date__lt=date.today(),
                        attended=False,
                        missed=False
                    )
        
        filters.extend([TodayVisitsFilter, OverdueFilter])
        return filters
    
    # Override save to auto-fill facility
    
    def save_model(self, request, obj, form, change):
        """Auto-fill facility from pregnancy if not set"""
        if not obj.facility:
            obj.facility = obj.pregnancy.facility
        
        if not obj.recorded_by and request.user.role == 'NURSE':
            obj.recorded_by = request.user
        
        super().save_model(request, obj, form, change)
        
        # Show helpful message
        if change and obj.attended:
            self.message_user(
                request,
                f"✓ ANC Visit {obj.visit_number} recorded for {obj.pregnancy.mother.full_name}"
            )


# Customize admin site header
admin.site.site_header = "Maternal Health System - ANC Management"