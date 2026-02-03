# apps/reminders/__init__.py
"""
Reminders App - SMS Notification Engine

This app handles:
- SMS reminder templates with placeholders
- Tracking all sent SMS reminders
- Delivery status monitoring
- Retry mechanism for failed messages
- System audit logging
- Daily cron job for automatic reminders

Key Models:
- ReminderTemplate: Reusable SMS templates
- SentReminder: Log of all SMS sent
- SystemLog: Audit trail for all actions

Management Commands:
- seed_reminder_templates: Create default templates
- send_daily_reminders: Daily cron job to check and send reminders
"""

default_app_config = 'apps.reminders.apps.RemindersConfig'