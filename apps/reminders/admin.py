# apps/reminders/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import ReminderTemplate, SentReminder, SystemLog


@admin.register(ReminderTemplate)
class ReminderTemplateAdmin(admin.ModelAdmin):
    """
    Admin interface for managing SMS templates
    Allows easy editing of message content and scheduling
    """
    
    list_display = [
        'reminder_type_display',
        'name',
        'message_preview',
        'timing_display',
        'is_active',
        'usage_count',
        'updated_at',
    ]
    
    list_filter = [
        'is_active',
        'reminder_type',
        'days_before',
    ]
    
    search_fields = [
        'name',
        'message_template',
        'description',
    ]
    
    readonly_fields = [
        'created_at',
        'updated_at',
        'usage_count',
        'preview_rendered_message',
    ]
    
    fieldsets = (
        ('Template Information', {
            'fields': (
                'reminder_type',
                'name',
                'is_active',
            )
        }),
        ('Message Content', {
            'fields': (
                'message_template',
                'preview_rendered_message',
            ),
            'description': (
                'Available placeholders: {name}, {visit_number}, {date}, {time}, '
                '{facility}, {vaccine_name}, {baby_name}, {weeks_pregnant}, {edd}'
            )
        }),
        ('Timing Configuration', {
            'fields': (
                'days_before',
                'send_time',
            ),
            'description': 'When to send this reminder relative to the appointment'
        }),
        ('Notes & Metadata', {
            'fields': (
                'description',
                'usage_count',
                'created_at',
                'updated_at',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_templates', 'deactivate_templates', 'test_render']
    
    def reminder_type_display(self, obj):
        """Display reminder type with color coding"""
        colors = {
            'ANC_UPCOMING': '#2196F3',
            'ANC_TODAY': '#4CAF50',
            'ANC_MISSED': '#F44336',
            'VACCINE_UPCOMING': '#9C27B0',
            'VACCINE_TODAY': '#673AB7',
            'VACCINE_MISSED': '#E91E63',
            'DELIVERY_APPROACHING': '#FF9800',
            'DANGER_SIGNS': '#F44336',
        }
        color = colors.get(obj.reminder_type, '#666')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; '
            'border-radius: 4px; font-size: 0.9em;">{}</span>',
            color,
            obj.get_reminder_type_display()
        )
    reminder_type_display.short_description = 'Type'
    
    def message_preview(self, obj):
        """Show first 60 characters of message"""
        preview = obj.message_template[:60]
        if len(obj.message_template) > 60:
            preview += '...'
        return format_html('<span style="color: #666; font-style: italic;">{}</span>', preview)
    message_preview.short_description = 'Message Preview'
    
    def timing_display(self, obj):
        """Display when message is sent"""
        if obj.days_before == 0:
            timing = "Same day"
        elif obj.days_before == 1:
            timing = "1 day before"
        else:
            timing = f"{obj.days_before} days before"
        
        return format_html(
            '{} at <strong>{}</strong>',
            timing,
            obj.send_time.strftime('%H:%M')
        )
    timing_display.short_description = 'Timing'
    
    def usage_count(self, obj):
        """Show how many times this template has been used"""
        count = obj.sent_reminders.count()
        return format_html('<span style="color: #2196F3; font-weight: bold;">{}</span>', count)
    usage_count.short_description = 'Times Used'
    
    def preview_rendered_message(self, obj):
        """Show example of rendered message"""
        # Sample context
        context = {
            'name': 'Mary',
            'visit_number': '2',
            'date': '15 May 2025',
            'time': '10:00 AM',
            'facility': 'Kibera Health Centre',
            'vaccine_name': 'BCG',
            'baby_name': 'Baby John',
            'weeks_pregnant': '24',
            'edd': '20 Aug 2025',
        }
        
        rendered = obj.render_message(context)
        return format_html(
            '<div style="background: #f5f5f5; padding: 10px; border-radius: 4px; '
            'font-family: monospace; white-space: pre-wrap;">{}</div>',
            rendered
        )
    preview_rendered_message.short_description = 'Preview (with sample data)'
    
    def get_queryset(self, request):
        """Annotate with usage count"""
        qs = super().get_queryset(request)
        return qs.annotate(usage=Count('sent_reminders'))
    
    # Custom Actions
    
    def activate_templates(self, request, queryset):
        """Activate selected templates"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f"✓ Activated {updated} template(s)")
    activate_templates.short_description = "✓ Activate selected templates"
    
    def deactivate_templates(self, request, queryset):
        """Deactivate selected templates"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"✗ Deactivated {updated} template(s)")
    deactivate_templates.short_description = "✗ Deactivate selected templates"
    
    def test_render(self, request, queryset):
        """Test rendering selected templates"""
        for template in queryset:
            context = {
                'name': 'Test User',
                'visit_number': '1',
                'date': 'Today',
                'facility': 'Test Facility',
            }
            rendered = template.render_message(context)
            self.message_user(
                request,
                f"{template.name}: {rendered[:100]}..."
            )
    test_render.short_description = "🔍 Test render selected templates"


@admin.register(SentReminder)
class SentReminderAdmin(admin.ModelAdmin):
    """
    Admin interface for viewing and managing sent SMS reminders
    Tracks delivery status, retries, and costs
    """
    
    list_display = [
        'status_icon',
        'mother_name',
        'reminder_type_display',
        'phone_display',
        'scheduled_vs_sent',
        'delivery_status_display',
        'retry_display',
        'cost_display',
        'facility',
    ]
    
    list_filter = [
        'delivery_status',
        'reminder_type',
        'is_manual',
        'facility',
        'scheduled_datetime',
        ('retry_count', admin.EmptyFieldListFilter),
    ]
    
    search_fields = [
        'mother__first_name',
        'mother__last_name',
        'phone_number',
        'message_content',
    ]
    
    readonly_fields = [
        'scheduled_datetime',
        'sent_datetime',
        'delivered_datetime',
        'delivery_time_seconds',
        'created_at',
        'updated_at',
        'message_preview',
    ]
    
    date_hierarchy = 'scheduled_datetime'
    
    ordering = ['-scheduled_datetime']
    
    fieldsets = (
        ('Recipient', {
            'fields': (
                'mother',
                'phone_number',
            )
        }),
        ('Reminder Details', {
            'fields': (
                'reminder_type',
                'message_content',
                'message_preview',
                'template_used',
            )
        }),
        ('Context (What this is about)', {
            'fields': (
                'pregnancy',
                'anc_visit',
                'baby',
                'immunization',
            ),
            'classes': ('collapse',)
        }),
        ('Timing', {
            'fields': (
                'scheduled_datetime',
                'sent_datetime',
                'delivered_datetime',
                'delivery_time_seconds',
            )
        }),
        ('Delivery Status', {
            'fields': (
                'delivery_status',
                'gateway_response',
                'gateway_message_id',
            )
        }),
        ('Retry Mechanism', {
            'fields': (
                'retry_count',
                'max_retries',
                'next_retry_datetime',
            ),
            'classes': ('collapse',)
        }),
        ('Cost & Metadata', {
            'fields': (
                'sms_cost',
                'facility',
                'sent_by',
                'is_manual',
            ),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'mark_as_sent',
        'mark_as_delivered',
        'mark_as_failed',
        'retry_failed',
        'export_to_csv',
    ]
    
    def status_icon(self, obj):
        """Display status with icon"""
        icons = {
            'PENDING': '⏳',
            'SENT': '📤',
            'DELIVERED': '✅',
            'FAILED': '❌',
            'INVALID_NUMBER': '⚠️',
            'REJECTED': '🚫',
        }
        colors = {
            'PENDING': '#FF9800',
            'SENT': '#2196F3',
            'DELIVERED': '#4CAF50',
            'FAILED': '#F44336',
            'INVALID_NUMBER': '#FF5722',
            'REJECTED': '#9E9E9E',
        }
        
        icon = icons.get(obj.delivery_status, '?')
        color = colors.get(obj.delivery_status, '#666')
        
        return format_html(
            '<span style="font-size: 1.5em;" title="{}">{}</span>',
            obj.get_delivery_status_display(),
            icon
        )
    status_icon.short_description = ''
    
    def mother_name(self, obj):
        """Display mother's name with link"""
        return format_html(
            '<a href="/admin/mothers/mother/{}/change/">{}</a>',
            obj.mother.id,
            obj.mother.full_name
        )
    mother_name.short_description = 'Mother'
    
    def reminder_type_display(self, obj):
        """Display reminder type with badge"""
        colors = {
            'ANC_UPCOMING': '#2196F3',
            'ANC_TODAY': '#4CAF50',
            'ANC_MISSED': '#F44336',
            'VACCINE_UPCOMING': '#9C27B0',
            'VACCINE_TODAY': '#673AB7',
            'VACCINE_MISSED': '#E91E63',
            'DELIVERY_APPROACHING': '#FF9800',
        }
        color = colors.get(obj.reminder_type, '#666')
        
        # Shortened labels for display
        short_labels = {
            'ANC_UPCOMING': 'ANC ⏰',
            'ANC_TODAY': 'ANC 📅',
            'ANC_MISSED': 'ANC ⚠️',
            'VACCINE_UPCOMING': 'VAX ⏰',
            'VACCINE_TODAY': 'VAX 📅',
            'VACCINE_MISSED': 'VAX ⚠️',
            'DELIVERY_APPROACHING': 'DEL 🤰',
        }
        label = short_labels.get(obj.reminder_type, obj.reminder_type)
        
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 6px; '
            'border-radius: 3px; font-size: 0.85em; white-space: nowrap;">{}</span>',
            color,
            label
        )
    reminder_type_display.short_description = 'Type'
    
    def phone_display(self, obj):
        """Display phone number"""
        return format_html(
            '<span style="font-family: monospace;">{}</span>',
            obj.phone_number
        )
    phone_display.short_description = 'Phone'
    
    def scheduled_vs_sent(self, obj):
        """Display scheduled vs actual send time"""
        scheduled = obj.scheduled_datetime.strftime('%d %b, %H:%M')
        
        if obj.sent_datetime:
            sent = obj.sent_datetime.strftime('%d %b, %H:%M')
            delay = (obj.sent_datetime - obj.scheduled_datetime).total_seconds() / 60
            
            if delay > 5:  # More than 5 minutes delay
                return format_html(
                    '<div>Scheduled: {}</div><div style="color: orange;">Sent: {} <small>(+{:.0f}m)</small></div>',
                    scheduled, sent, delay
                )
            else:
                return format_html(
                    '<div>Scheduled: {}</div><div style="color: green;">Sent: {}</div>',
                    scheduled, sent
                )
        else:
            return format_html(
                '<div>Scheduled: {}</div><div style="color: gray;">Not sent yet</div>',
                scheduled
            )
    scheduled_vs_sent.short_description = 'Timing'
    
    def delivery_status_display(self, obj):
        """Display delivery status with color"""
        colors = {
            'PENDING': '#FF9800',
            'SENT': '#2196F3',
            'DELIVERED': '#4CAF50',
            'FAILED': '#F44336',
            'INVALID_NUMBER': '#FF5722',
            'REJECTED': '#9E9E9E',
        }
        color = colors.get(obj.delivery_status, '#666')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_delivery_status_display()
        )
    delivery_status_display.short_description = 'Status'
    
    def retry_display(self, obj):
        """Display retry information"""
        if obj.retry_count == 0:
            return '-'
        
        return format_html(
            '<span style="color: {};">{}/{}</span>',
            '#F44336' if obj.retry_count >= obj.max_retries else '#FF9800',
            obj.retry_count,
            obj.max_retries
        )
    retry_display.short_description = 'Retries'
    
    def cost_display(self, obj):
        """Display SMS cost"""
        if obj.sms_cost:
            return format_html(
                '<span style="color: #4CAF50;">KES {:.2f}</span>',
                obj.sms_cost
            )
        return '-'
    cost_display.short_description = 'Cost'
    
    def context_display(self, obj):
        """Display what this reminder was about"""
        return obj.get_context_display()
    context_display.short_description = 'Context'
    
    def message_preview(self, obj):
        """Display message in a nice box"""
        return format_html(
            '<div style="background: #f5f5f5; padding: 10px; border-radius: 4px; '
            'border-left: 3px solid #2196F3; max-width: 500px; '
            'font-family: Arial, sans-serif; line-height: 1.5;">{}</div>',
            obj.message_content
        )
    message_preview.short_description = 'Message Content'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'mother',
            'facility',
            'template_used',
            'pregnancy',
            'anc_visit',
            'baby',
            'immunization',
            'sent_by'
        )
    
    # Custom Actions
    
    def mark_as_sent(self, request, queryset):
        """Mark selected reminders as sent"""
        count = 0
        for reminder in queryset.filter(delivery_status='PENDING'):
            reminder.mark_as_sent()
            count += 1
        self.message_user(request, f"✓ Marked {count} reminder(s) as SENT")
    mark_as_sent.short_description = "📤 Mark as SENT"
    
    def mark_as_delivered(self, request, queryset):
        """Mark selected reminders as delivered"""
        count = 0
        for reminder in queryset.filter(delivery_status='SENT'):
            reminder.mark_as_delivered()
            count += 1
        self.message_user(request, f"✓ Marked {count} reminder(s) as DELIVERED")
    mark_as_delivered.short_description = "✅ Mark as DELIVERED"
    
    def mark_as_failed(self, request, queryset):
        """Mark selected reminders as failed"""
        count = 0
        for reminder in queryset.exclude(delivery_status='DELIVERED'):
            reminder.mark_as_failed(reason="Manually marked as failed by admin")
            count += 1
        self.message_user(request, f"❌ Marked {count} reminder(s) as FAILED")
    mark_as_failed.short_description = "❌ Mark as FAILED"
    
    def retry_failed(self, request, queryset):
        """Retry failed reminders"""
        count = 0
        for reminder in queryset.filter(delivery_status='FAILED'):
            if reminder.retry_count < reminder.max_retries:
                reminder.delivery_status = 'PENDING'
                reminder.next_retry_datetime = timezone.now()
                reminder.save()
                count += 1
        self.message_user(request, f"🔄 Queued {count} reminder(s) for retry")
    retry_failed.short_description = "🔄 Retry failed reminders"
    
    def export_to_csv(self, request, queryset):
        """Export selected reminders to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="sent_reminders.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Mother', 'Phone', 'Type', 'Message', 'Scheduled', 
            'Sent', 'Status', 'Cost', 'Facility'
        ])
        
        for reminder in queryset:
            writer.writerow([
                reminder.mother.full_name,
                reminder.phone_number,
                reminder.get_reminder_type_display(),
                reminder.message_content,
                reminder.scheduled_datetime.strftime('%Y-%m-%d %H:%M'),
                reminder.sent_datetime.strftime('%Y-%m-%d %H:%M') if reminder.sent_datetime else '',
                reminder.get_delivery_status_display(),
                str(reminder.sms_cost) if reminder.sms_cost else '',
                reminder.facility.name,
            ])
        
        self.message_user(request, f"✓ Exported {queryset.count()} reminders to CSV")
        return response
    export_to_csv.short_description = "📥 Export to CSV"
    
    # Custom Filters
    
    def get_list_filter(self, request):
        """Add custom filters"""
        filters = list(self.list_filter)
        
        class TodayRemindersFilter(admin.SimpleListFilter):
            title = "Today's Reminders"
            parameter_name = 'today'
            
            def lookups(self, request, model_admin):
                return (
                    ('yes', 'Scheduled Today'),
                    ('sent', 'Sent Today'),
                )
            
            def queryset(self, request, queryset):
                today = timezone.now().date()
                if self.value() == 'yes':
                    return queryset.filter(scheduled_datetime__date=today)
                elif self.value() == 'sent':
                    return queryset.filter(sent_datetime__date=today)
        
        class DeliveryRateFilter(admin.SimpleListFilter):
            title = 'Delivery Success'
            parameter_name = 'delivery_success'
            
            def lookups(self, request, model_admin):
                return (
                    ('delivered', 'Successfully Delivered'),
                    ('failed', 'Failed/Rejected'),
                    ('pending', 'Still Pending'),
                )
            
            def queryset(self, request, queryset):
                if self.value() == 'delivered':
                    return queryset.filter(delivery_status='DELIVERED')
                elif self.value() == 'failed':
                    return queryset.filter(
                        delivery_status__in=['FAILED', 'REJECTED', 'INVALID_NUMBER']
                    )
                elif self.value() == 'pending':
                    return queryset.filter(delivery_status='PENDING')
        
        filters.extend([TodayRemindersFilter, DeliveryRateFilter])
        return filters


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    """
    Admin interface for system audit logs
    Read-only for security and compliance
    """
    
    list_display = [
        'timestamp_display',
        'log_level_display',
        'user_display',
        'action_display',
        'model_affected',
        'description_preview',
        'facility',
    ]
    
    list_filter = [
        'log_level',
        'action_type',
        'facility',
        'timestamp',
        'user',
    ]
    
    search_fields = [
        'user__username',
        'description',
        'model_name',
        'object_id',
        'ip_address',
    ]
    
    readonly_fields = [
        'user',
        'action_type',
        'log_level',
        'model_name',
        'object_id',
        'description',
        'ip_address',
        'user_agent',
        'metadata',
        'timestamp',
        'facility',
    ]
    
    date_hierarchy = 'timestamp'
    
    ordering = ['-timestamp']
    
    # Make logs read-only - cannot be edited or deleted
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        # Only superusers can delete logs (for cleanup)
        return request.user.is_superuser
    
    fieldsets = (
        ('Who & When', {
            'fields': ('user', 'timestamp', 'facility')
        }),
        ('What Happened', {
            'fields': ('action_type', 'log_level', 'description')
        }),
        ('What Was Affected', {
            'fields': ('model_name', 'object_id'),
            'classes': ('collapse',)
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'metadata'),
            'classes': ('collapse',)
        }),
    )
    
    def timestamp_display(self, obj):
        """Display timestamp with relative time"""
        return format_html(
            '<div>{}</div><small style="color: #666;">{}</small>',
            obj.timestamp.strftime('%d %b %Y, %H:%M:%S'),
            timezone.now() - obj.timestamp
        )
    timestamp_display.short_description = 'When'
    
    def log_level_display(self, obj):
        """Display log level with color"""
        colors = {
            'INFO': '#2196F3',
            'WARNING': '#FF9800',
            'ERROR': '#F44336',
            'CRITICAL': '#9C27B0',
        }
        color = colors.get(obj.log_level, '#666')
        
        icons = {
            'INFO': 'ℹ️',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🔥',
        }
        icon = icons.get(obj.log_level, '•')
        
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} {}</span>',
            color, icon, obj.get_log_level_display()
        )
    log_level_display.short_description = 'Level'
    
    def user_display(self, obj):
        """Display user or SYSTEM"""
        if obj.user:
            return format_html(
                '<a href="/admin/users/customuser/{}/change/">{}</a>',
                obj.user.id,
                obj.user.username
            )
        return format_html('<em style="color: #666;">SYSTEM</em>')
    user_display.short_description = 'User'
    
    def action_display(self, obj):
        """Display action type with icon"""
        icons = {
            'LOGIN': '🔓',
            'LOGOUT': '🔒',
            'LOGIN_FAILED': '🚫',
            'CREATE': '➕',
            'UPDATE': '✏️',
            'DELETE': '🗑️',
            'SMS_SENT': '📤',
            'SMS_FAILED': '❌',
            'DANGER_SIGN': '⚠️',
            'CRON_RUN': '⏰',
        }
        icon = icons.get(obj.action_type, '•')
        
        return format_html(
            '{} <span style="font-weight: 500;">{}</span>',
            icon,
            obj.get_action_type_display()
        )
    action_display.short_description = 'Action'
    
    def model_affected(self, obj):
        """Display model and object ID"""
        if obj.model_name:
            return format_html(
                '<span style="font-family: monospace;">{}</span> '
                '<small style="color: #666;">(ID: {})</small>',
                obj.model_name,
                obj.object_id or '-'
            )
        return '-'
    model_affected.short_description = 'Model'
    
    def description_preview(self, obj):
        """Show first 80 characters"""
        preview = obj.description[:80]
        if len(obj.description) > 80:
            preview += '...'
        return preview
    description_preview.short_description = 'Description'
    
    def get_queryset(self, request):
        """Optimize queries"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'facility')


# Customize admin site
admin.site.site_header = "Maternal Health System - SMS & Reminders"
admin.site.site_title = "SMS Management"
admin.site.index_title = "SMS Notification Engine"