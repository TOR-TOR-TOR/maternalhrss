# apps/reminders/models.py
from django.db import models
from django.utils import timezone
from datetime import datetime, date, timedelta
from apps.users.models import CustomUser, Facility
from apps.mothers.models import Mother, Pregnancy
from apps.anc.models import ANCVisit
from apps.delivery.models import Baby
from apps.immunization.models import ImmunizationSchedule


class ReminderTemplate(models.Model):
    """
    SMS message templates with placeholders for personalization
    Allows easy message editing without code changes
    """
    
    REMINDER_TYPES = [
        ('ANC_UPCOMING', 'ANC Visit Upcoming (3 days before)'),
        ('ANC_TODAY', 'ANC Visit Today'),
        ('ANC_MISSED', 'ANC Visit Missed (Follow-up)'),
        ('VACCINE_UPCOMING', 'Vaccination Upcoming (3 days before)'),
        ('VACCINE_TODAY', 'Vaccination Today'),
        ('VACCINE_MISSED', 'Vaccination Missed (Follow-up)'),
        ('PNC_UPCOMING', 'Postnatal Care Upcoming'),
        ('DANGER_SIGNS', 'Danger Signs Alert'),
        ('DELIVERY_APPROACHING', 'Delivery Approaching (2 weeks)'),
        ('OVERDUE_PREGNANCY', 'Pregnancy Overdue'),
        ('GENERAL', 'General Reminder'),
    ]
    
    # Template Information
    reminder_type = models.CharField(
        max_length=30,
        choices=REMINDER_TYPES,
        unique=True,
        help_text="Type of reminder this template is for"
    )
    name = models.CharField(
        max_length=200,
        help_text="Template name for easy identification"
    )
    
    # Message Content
    message_template = models.TextField(
        help_text=(
            "SMS template with placeholders:\n"
            "{name} - Mother's name\n"
            "{visit_number} - ANC visit number\n"
            "{date} - Appointment date\n"
            "{time} - Appointment time\n"
            "{facility} - Facility name\n"
            "{vaccine_name} - Vaccine name\n"
            "{baby_name} - Baby's name\n"
            "{weeks_pregnant} - Gestational age\n"
            "{edd} - Expected due date"
        )
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Is this template currently active?"
    )
    
    # Timing Configuration
    days_before = models.IntegerField(
        default=3,
        help_text="How many days before appointment to send (0 = same day)"
    )
    send_time = models.TimeField(
        default="09:00:00",
        help_text="What time of day to send (24-hour format)"
    )
    
    # Metadata
    description = models.TextField(
        blank=True,
        help_text="Internal notes about this template"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'reminder_templates'
        ordering = ['reminder_type']
        verbose_name = 'Reminder Template'
        verbose_name_plural = 'Reminder Templates'
    
    def __str__(self):
        status = "✓ Active" if self.is_active else "✗ Inactive"
        return f"{self.get_reminder_type_display()} ({status})"
    
    def render_message(self, context):
        """
        Render template with actual values
        
        Args:
            context (dict): Dictionary with placeholder values
            
        Returns:
            str: Rendered message with placeholders replaced
        """
        message = self.message_template
        
        # Replace all placeholders in the template
        for key, value in context.items():
            placeholder = f"{{{key}}}"
            if placeholder in message:
                message = message.replace(placeholder, str(value))
        
        return message
    
    @classmethod
    def get_active_template(cls, reminder_type):
        """Get active template for a specific reminder type"""
        try:
            return cls.objects.get(reminder_type=reminder_type, is_active=True)
        except cls.DoesNotExist:
            return None


class SentReminder(models.Model):
    """
    Complete log of every SMS sent by the system
    Tracks delivery status, retries, and costs
    """
    
    REMINDER_TYPES = [
        ('ANC_UPCOMING', 'ANC Visit Upcoming'),
        ('ANC_TODAY', 'ANC Visit Today'),
        ('ANC_MISSED', 'ANC Visit Missed'),
        ('VACCINE_UPCOMING', 'Vaccination Upcoming'),
        ('VACCINE_TODAY', 'Vaccination Today'),
        ('VACCINE_MISSED', 'Vaccination Missed'),
        ('PNC_UPCOMING', 'Postnatal Care Upcoming'),
        ('DANGER_SIGNS', 'Danger Signs Alert'),
        ('DELIVERY_APPROACHING', 'Delivery Approaching'),
        ('OVERDUE_PREGNANCY', 'Pregnancy Overdue'),
        ('GENERAL', 'General Reminder'),
    ]
    
    DELIVERY_STATUS = [
        ('PENDING', 'Pending (not sent yet)'),
        ('SENT', 'Sent to gateway'),
        ('DELIVERED', 'Delivered to phone'),
        ('FAILED', 'Failed to send'),
        ('INVALID_NUMBER', 'Invalid phone number'),
        ('REJECTED', 'Rejected by gateway'),
    ]
    
    # Recipient Information
    mother = models.ForeignKey(
        Mother,
        on_delete=models.CASCADE,
        related_name='reminders_received',
        help_text="Mother who received this SMS"
    )
    phone_number = models.CharField(
        max_length=15,
        help_text="Phone number SMS was sent to"
    )
    
    # Reminder Details
    reminder_type = models.CharField(
        max_length=30,
        choices=REMINDER_TYPES,
        help_text="Type of reminder"
    )
    message_content = models.TextField(
        help_text="Actual SMS text that was sent"
    )
    template_used = models.ForeignKey(
        ReminderTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_reminders',
        help_text="Template used to generate this message"
    )
    
    # Context Links (what this reminder was about)
    pregnancy = models.ForeignKey(
        Pregnancy,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reminders',
        help_text="Related pregnancy (if applicable)"
    )
    anc_visit = models.ForeignKey(
        ANCVisit,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reminders',
        help_text="Related ANC visit (if applicable)"
    )
    baby = models.ForeignKey(
        Baby,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reminders',
        help_text="Related baby (if applicable)"
    )
    immunization = models.ForeignKey(
        ImmunizationSchedule,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reminders',
        help_text="Related immunization (if applicable)"
    )
    
    # Timing
    scheduled_datetime = models.DateTimeField(
        help_text="When system scheduled this SMS to be sent"
    )
    sent_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When SMS was actually sent to gateway"
    )
    delivered_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When SMS was delivered to phone (if confirmed)"
    )
    
    # Delivery Status
    delivery_status = models.CharField(
        max_length=20,
        choices=DELIVERY_STATUS,
        default='PENDING',
        help_text="Current status of this SMS"
    )
    gateway_response = models.TextField(
        blank=True,
        help_text="Response from SMS gateway (Africa's Talking, etc.)"
    )
    gateway_message_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Message ID from gateway for tracking"
    )
    
    # Retry Mechanism
    retry_count = models.IntegerField(
        default=0,
        help_text="Number of times sending was retried"
    )
    max_retries = models.IntegerField(
        default=3,
        help_text="Maximum number of retry attempts"
    )
    next_retry_datetime = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When to retry if failed"
    )
    
    # Cost Tracking
    sms_cost = models.DecimalField(
        max_digits=6,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Cost of this SMS (in KES)"
    )
    
    # Facility & Staff
    facility = models.ForeignKey(
        Facility,
        on_delete=models.PROTECT,
        related_name='sent_reminders',
        help_text="Facility that initiated this reminder"
    )
    sent_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reminders_sent',
        help_text="User who triggered this reminder (if manual)"
    )
    is_manual = models.BooleanField(
        default=False,
        help_text="Was this sent manually or auto-generated?"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sent_reminders'
        ordering = ['-scheduled_datetime']
        verbose_name = 'Sent Reminder'
        verbose_name_plural = 'Sent Reminders'
        indexes = [
            models.Index(fields=['mother', 'reminder_type']),
            models.Index(fields=['delivery_status']),
            models.Index(fields=['scheduled_datetime']),
            models.Index(fields=['facility', 'sent_datetime']),
            models.Index(fields=['phone_number']),
        ]
    
    def __str__(self):
        status_icons = {
            'PENDING': '⏳',
            'SENT': '📤',
            'DELIVERED': '✓',
            'FAILED': '✗',
            'INVALID_NUMBER': '⚠',
            'REJECTED': '🚫',
        }
        icon = status_icons.get(self.delivery_status, '?')
        return f"{icon} {self.get_reminder_type_display()} to {self.mother.full_name} ({self.delivery_status})"
    
    def mark_as_sent(self, gateway_response=None, message_id=None):
        """Mark SMS as sent to gateway"""
        self.delivery_status = 'SENT'
        self.sent_datetime = timezone.now()
        if gateway_response:
            self.gateway_response = gateway_response
        if message_id:
            self.gateway_message_id = message_id
        self.save()
    
    def mark_as_delivered(self):
        """Mark SMS as delivered to phone"""
        self.delivery_status = 'DELIVERED'
        self.delivered_datetime = timezone.now()
        self.save()
    
    def mark_as_failed(self, reason=None):
        """Mark SMS as failed and schedule retry if possible"""
        self.delivery_status = 'FAILED'
        if reason:
            self.gateway_response = reason
        
        # Schedule retry if not exceeded max attempts
        if self.retry_count < self.max_retries:
            self.retry_count += 1
            # Exponential backoff: 1 hour, 2 hours, 4 hours
            retry_delay = timedelta(hours=2 ** self.retry_count)
            self.next_retry_datetime = timezone.now() + retry_delay
        
        self.save()
    
    @property
    def is_pending(self):
        """Check if SMS is pending"""
        return self.delivery_status == 'PENDING'
    
    @property
    def is_delivered(self):
        """Check if SMS was delivered"""
        return self.delivery_status == 'DELIVERED'
    
    @property
    def needs_retry(self):
        """Check if SMS needs to be retried"""
        if self.delivery_status != 'FAILED':
            return False
        if self.retry_count >= self.max_retries:
            return False
        if not self.next_retry_datetime:
            return False
        return timezone.now() >= self.next_retry_datetime
    
    @property
    def delivery_time_seconds(self):
        """Calculate how long it took to deliver (if delivered)"""
        if self.sent_datetime and self.delivered_datetime:
            return (self.delivered_datetime - self.sent_datetime).total_seconds()
        return None
    
    def get_context_display(self):
        """Get human-readable context of what this reminder was about"""
        if self.anc_visit:
            return f"ANC Visit {self.anc_visit.visit_number}"
        elif self.immunization:
            return f"Vaccine: {self.immunization.vaccine.name}"
        elif self.baby:
            return f"Baby: {self.baby.display_name}"
        elif self.pregnancy:
            return f"Pregnancy (Week {self.pregnancy.gestational_age_weeks})"
        return "General"


class SystemLog(models.Model):
    """
    Audit trail for all system actions
    Tracks user activities for security and troubleshooting
    """
    
    ACTION_TYPES = [
        # User Actions
        ('LOGIN', 'User Login'),
        ('LOGOUT', 'User Logout'),
        ('LOGIN_FAILED', 'Failed Login Attempt'),
        
        # Data Operations
        ('CREATE', 'Record Created'),
        ('UPDATE', 'Record Updated'),
        ('DELETE', 'Record Deleted'),
        ('VIEW', 'Record Viewed'),
        
        # SMS Operations
        ('SMS_SENT', 'SMS Sent'),
        ('SMS_FAILED', 'SMS Failed'),
        ('SMS_DELIVERED', 'SMS Delivered'),
        
        # System Events
        ('CRON_RUN', 'Cron Job Executed'),
        ('BULK_UPDATE', 'Bulk Update Performed'),
        ('EXPORT', 'Data Exported'),
        ('IMPORT', 'Data Imported'),
        
        # Alerts
        ('DANGER_SIGN', 'Danger Sign Flagged'),
        ('MISSED_VISIT', 'Visit Marked as Missed'),
        ('OVERDUE_PREGNANCY', 'Pregnancy Marked as Overdue'),
    ]
    
    LOG_LEVELS = [
        ('INFO', 'Information'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    ]
    
    # Who
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_logs',
        help_text="User who performed the action (null for system actions)"
    )
    
    # What
    action_type = models.CharField(
        max_length=30,
        choices=ACTION_TYPES,
        help_text="Type of action performed"
    )
    log_level = models.CharField(
        max_length=20,
        choices=LOG_LEVELS,
        default='INFO',
        help_text="Severity level of this log entry"
    )
    
    # Where (What was affected)
    model_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of the model that was affected"
    )
    object_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID of the specific record affected"
    )
    
    # Details
    description = models.TextField(
        help_text="Detailed description of what happened"
    )
    
    # Technical Details
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the user (if applicable)"
    )
    user_agent = models.TextField(
        blank=True,
        help_text="Browser/device information (if applicable)"
    )
    
    # Additional Context (JSON)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context data (JSON format)"
    )
    
    # When
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When this action occurred"
    )
    
    # Facility Context
    facility = models.ForeignKey(
        Facility,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='system_logs',
        help_text="Facility where action occurred (if applicable)"
    )
    
    class Meta:
        db_table = 'system_logs'
        ordering = ['-timestamp']
        verbose_name = 'System Log'
        verbose_name_plural = 'System Logs'
        indexes = [
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action_type', 'timestamp']),
            models.Index(fields=['model_name', 'object_id']),
            models.Index(fields=['log_level']),
            models.Index(fields=['facility', 'timestamp']),
        ]
    
    def __str__(self):
        user_str = self.user.username if self.user else "SYSTEM"
        return f"[{self.log_level}] {user_str}: {self.get_action_type_display()} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
    
    @classmethod
    def log_action(cls, action_type, description, user=None, model_name=None, 
                   object_id=None, log_level='INFO', facility=None, metadata=None):
        """
        Convenient method to create a log entry
        
        Usage:
            SystemLog.log_action(
                action_type='SMS_SENT',
                description='SMS reminder sent to Mary for ANC 2',
                user=request.user,
                log_level='INFO',
                metadata={'phone': '+254712...', 'cost': 0.8}
            )
        """
        return cls.objects.create(
            user=user,
            action_type=action_type,
            log_level=log_level,
            model_name=model_name,
            object_id=object_id,
            description=description,
            facility=facility,
            metadata=metadata or {}
        )
    
    @classmethod
    def log_sms(cls, reminder, user=None):
        """Log an SMS being sent"""
        return cls.log_action(
            action_type='SMS_SENT',
            description=f"SMS sent to {reminder.mother.full_name} ({reminder.phone_number}) - {reminder.get_reminder_type_display()}",
            user=user,
            model_name='SentReminder',
            object_id=str(reminder.id),
            facility=reminder.facility,
            metadata={
                'phone': reminder.phone_number,
                'reminder_type': reminder.reminder_type,
                'mother_id': reminder.mother.id,
            }
        )
    
    @classmethod
    def log_login(cls, user, ip_address=None, user_agent=None, success=True):
        """Log a login attempt"""
        return cls.log_action(
            action_type='LOGIN' if success else 'LOGIN_FAILED',
            description=f"User {user.username} {'logged in' if success else 'failed to log in'}",
            user=user if success else None,
            log_level='INFO' if success else 'WARNING',
            facility=user.facility if success else None,
            metadata={
                'ip_address': ip_address,
                'user_agent': user_agent,
            }
        )
    
    @classmethod
    def log_danger_sign(cls, anc_visit, user):
        """Log when a danger sign is flagged"""
        return cls.log_action(
            action_type='DANGER_SIGN',
            description=f"Danger signs flagged for {anc_visit.pregnancy.mother.full_name} at ANC {anc_visit.visit_number}",
            user=user,
            model_name='ANCVisit',
            object_id=str(anc_visit.id),
            log_level='WARNING',
            facility=anc_visit.facility,
            metadata={
                'mother_id': anc_visit.pregnancy.mother.id,
                'visit_number': anc_visit.visit_number,
                'notes': anc_visit.danger_signs_notes,
            }
        )


# ============================================================================
# UTILITY FUNCTIONS FOR REMINDER MANAGEMENT
# ============================================================================

def get_pending_reminders():
    """
    Get all reminders that need to be sent now
    Used by cron job to send scheduled reminders
    """
    now = timezone.now()
    
    return SentReminder.objects.filter(
        delivery_status='PENDING',
        scheduled_datetime__lte=now
    ).select_related('mother', 'facility', 'template_used')


def get_failed_reminders_for_retry():
    """
    Get all failed reminders that are ready for retry
    """
    now = timezone.now()
    
    return SentReminder.objects.filter(
        delivery_status='FAILED',
        retry_count__lt=models.F('max_retries'),
        next_retry_datetime__lte=now
    ).select_related('mother', 'facility')


def create_anc_reminder(anc_visit, reminder_type='ANC_UPCOMING'):
    """
    Create a reminder for an ANC visit
    
    Args:
        anc_visit: ANCVisit instance
        reminder_type: Type of reminder (ANC_UPCOMING, ANC_TODAY, ANC_MISSED)
    """
    # Get the appropriate template
    template = ReminderTemplate.get_active_template(reminder_type)
    if not template:
        print(f"⚠ No active template found for {reminder_type}")
        return None
    
    # Prepare context for template
    context = {
        'name': anc_visit.pregnancy.mother.first_name,
        'visit_number': anc_visit.visit_number,
        'date': anc_visit.scheduled_date.strftime('%d %b %Y'),
        'facility': anc_visit.facility.name,
        'weeks_pregnant': anc_visit.pregnancy.gestational_age_weeks,
    }
    
    # Render message
    message = template.render_message(context)
    
    # Calculate when to send
    scheduled_datetime = timezone.now()
    if reminder_type == 'ANC_UPCOMING':
        # Send 3 days before at 9 AM
        send_date = anc_visit.scheduled_date - timedelta(days=template.days_before)
        scheduled_datetime = timezone.make_aware(
            datetime.combine(send_date, template.send_time)
        )
    
    # Create reminder record
    reminder = SentReminder.objects.create(
        mother=anc_visit.pregnancy.mother,
        phone_number=anc_visit.pregnancy.mother.phone_number,
        reminder_type=reminder_type,
        message_content=message,
        template_used=template,
        pregnancy=anc_visit.pregnancy,
        anc_visit=anc_visit,
        scheduled_datetime=scheduled_datetime,
        facility=anc_visit.facility,
    )
    
    return reminder


def create_vaccine_reminder(immunization, reminder_type='VACCINE_UPCOMING'):
    """
    Create a reminder for a vaccination appointment
    
    Args:
        immunization: ImmunizationSchedule instance
        reminder_type: Type of reminder
    """
    template = ReminderTemplate.get_active_template(reminder_type)
    if not template:
        return None
    
    context = {
        'name': immunization.baby.mother.first_name,
        'baby_name': immunization.baby.display_name,
        'vaccine_name': immunization.vaccine.name,
        'date': immunization.scheduled_date.strftime('%d %b %Y'),
        'facility': immunization.facility.name,
    }
    
    message = template.render_message(context)
    
    # Calculate when to send
    scheduled_datetime = timezone.now()
    if reminder_type == 'VACCINE_UPCOMING':
        send_date = immunization.scheduled_date - timedelta(days=template.days_before)
        scheduled_datetime = timezone.make_aware(
            datetime.combine(send_date, template.send_time)
        )
    
    reminder = SentReminder.objects.create(
        mother=immunization.baby.mother,
        phone_number=immunization.baby.mother.phone_number,
        reminder_type=reminder_type,
        message_content=message,
        template_used=template,
        baby=immunization.baby,
        immunization=immunization,
        scheduled_datetime=scheduled_datetime,
        facility=immunization.facility,
    )
    
    return reminder


def create_delivery_approaching_reminder(pregnancy):
    """
    Create a reminder when delivery is approaching (2 weeks)
    """
    template = ReminderTemplate.get_active_template('DELIVERY_APPROACHING')
    if not template:
        return None
    
    context = {
        'name': pregnancy.mother.first_name,
        'weeks_pregnant': pregnancy.gestational_age_weeks,
        'edd': pregnancy.edd.strftime('%d %b %Y'),
        'facility': pregnancy.facility.name,
    }
    
    message = template.render_message(context)
    
    reminder = SentReminder.objects.create(
        mother=pregnancy.mother,
        phone_number=pregnancy.mother.phone_number,
        reminder_type='DELIVERY_APPROACHING',
        message_content=message,
        template_used=template,
        pregnancy=pregnancy,
        scheduled_datetime=timezone.now(),
        facility=pregnancy.facility,
    )
    
    return reminder