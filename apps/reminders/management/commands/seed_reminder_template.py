# apps/reminders/management/commands/seed_reminder_templates.py
"""
Management command to create default SMS reminder templates
Run once after setting up the reminders app:
    python manage.py seed_reminder_templates

This creates professional, clear SMS templates following Kenya MOH guidelines
"""

from django.core.management.base import BaseCommand
from apps.reminders.models import ReminderTemplate


class Command(BaseCommand):
    help = 'Create default SMS reminder templates'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('📝 CREATING DEFAULT SMS TEMPLATES'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        templates = [
            {
                'reminder_type': 'ANC_UPCOMING',
                'name': 'ANC Visit Upcoming (3 days before)',
                'message_template': (
                    'Dear {name}, this is a reminder for your ANC Contact {visit_number} '
                    'on {date} at {facility}. Please attend for your health and baby\'s wellbeing. '
                    'Bring your Mother & Child booklet.'
                ),
                'days_before': 3,
                'send_time': '09:00:00',
                'description': 'Sent 3 days before scheduled ANC visit',
            },
            {
                'reminder_type': 'ANC_TODAY',
                'name': 'ANC Visit Today',
                'message_template': (
                    'Dear {name}, your ANC Contact {visit_number} is scheduled TODAY at {facility}. '
                    'Please attend. For any issues, contact {facility}. Stay healthy!'
                ),
                'days_before': 0,
                'send_time': '08:00:00',
                'description': 'Sent on the day of ANC visit',
            },
            {
                'reminder_type': 'ANC_MISSED',
                'name': 'ANC Visit Missed (Follow-up)',
                'message_template': (
                    'Dear {name}, we noticed you missed ANC Contact {visit_number} at {facility}. '
                    'Your health and baby\'s wellbeing are important. Please visit us soon or call for rescheduling. '
                    'We care about you.'
                ),
                'days_before': 0,
                'send_time': '10:00:00',
                'description': 'Follow-up for missed ANC visit',
            },
            {
                'reminder_type': 'VACCINE_UPCOMING',
                'name': 'Vaccination Upcoming (3 days before)',
                'message_template': (
                    'Dear {name}, reminder: {baby_name} is due for {vaccine_name} vaccination on {date} '
                    'at {facility}. Vaccines protect your baby from serious diseases. Please attend.'
                ),
                'days_before': 3,
                'send_time': '09:00:00',
                'description': 'Sent 3 days before vaccination appointment',
            },
            {
                'reminder_type': 'VACCINE_TODAY',
                'name': 'Vaccination Today',
                'message_template': (
                    'Dear {name}, {baby_name} is scheduled for {vaccine_name} vaccination TODAY at {facility}. '
                    'Please come. Bring the vaccination card. Keep your baby healthy!'
                ),
                'days_before': 0,
                'send_time': '08:00:00',
                'description': 'Sent on vaccination day',
            },
            {
                'reminder_type': 'VACCINE_MISSED',
                'name': 'Vaccination Missed (Follow-up)',
                'message_template': (
                    'Dear {name}, {baby_name} missed {vaccine_name} vaccination at {facility}. '
                    'Vaccines are crucial for your baby\'s health. Please visit us to catch up. '
                    'Call if you need help.'
                ),
                'days_before': 0,
                'send_time': '10:00:00',
                'description': 'Follow-up for missed vaccination',
            },
            {
                'reminder_type': 'DELIVERY_APPROACHING',
                'name': 'Delivery Approaching (38+ weeks)',
                'message_template': (
                    'Dear {name}, you are now {weeks_pregnant} weeks pregnant. Your delivery is near! '
                    'Expected date: {edd}. Prepare your delivery bag and plan transport to {facility}. '
                    'Come immediately if you experience labor signs.'
                ),
                'days_before': 0,
                'send_time': '09:00:00',
                'description': 'Sent weekly from week 38 onwards',
            },
            {
                'reminder_type': 'OVERDUE_PREGNANCY',
                'name': 'Pregnancy Overdue (40+ weeks)',
                'message_template': (
                    'Dear {name}, you are {weeks_pregnant} weeks pregnant (past your due date: {edd}). '
                    'PLEASE VISIT {facility} IMMEDIATELY for assessment. Your and baby\'s safety is our priority. '
                    'Come urgently or call us.'
                ),
                'days_before': 0,
                'send_time': '08:00:00',
                'description': 'Urgent reminder for overdue pregnancy',
            },
            {
                'reminder_type': 'DANGER_SIGNS',
                'name': 'Danger Signs Alert',
                'message_template': (
                    'Dear {name}, you were flagged with danger signs at your last visit. '
                    'URGENT: Please come to {facility} immediately or call us. Your health needs immediate attention. '
                    'Do not delay.'
                ),
                'days_before': 0,
                'send_time': '08:00:00',
                'description': 'Urgent alert for danger signs',
            },
            {
                'reminder_type': 'PNC_UPCOMING',
                'name': 'Postnatal Care Upcoming',
                'message_template': (
                    'Dear {name}, reminder for your postnatal check-up on {date} at {facility}. '
                    'Bring {baby_name} for baby check-up too. Both mother and baby health checks are important. '
                    'See you soon!'
                ),
                'days_before': 3,
                'send_time': '09:00:00',
                'description': 'Reminder for postnatal care visit',
            },
            {
                'reminder_type': 'GENERAL',
                'name': 'General Reminder',
                'message_template': (
                    'Dear {name}, this is a reminder from {facility}. Please contact us if you need any assistance. '
                    'Your health and your baby\'s health are our priority. Stay well!'
                ),
                'days_before': 0,
                'send_time': '09:00:00',
                'description': 'Generic template for custom messages',
            },
        ]
        
        created_count = 0
        updated_count = 0
        
        for template_data in templates:
            template, created = ReminderTemplate.objects.update_or_create(
                reminder_type=template_data['reminder_type'],
                defaults={
                    'name': template_data['name'],
                    'message_template': template_data['message_template'],
                    'days_before': template_data['days_before'],
                    'send_time': template_data['send_time'],
                    'description': template_data['description'],
                    'is_active': True,
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created: {template.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'  ↻ Updated: {template.name}')
                )
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS(f'📊 SUMMARY'))
        self.stdout.write('='*70 + '\n')
        self.stdout.write(f'Created: {created_count}')
        self.stdout.write(f'Updated: {updated_count}')
        self.stdout.write(f'Total: {created_count + updated_count}\n')
        self.stdout.write(self.style.SUCCESS('✅ All templates ready!\n'))
        
        # Show sample preview
        self.stdout.write(self.style.HTTP_INFO('\n📱 SAMPLE PREVIEW:'))
        self.stdout.write('-'*70)
        sample_template = ReminderTemplate.objects.get(reminder_type='ANC_UPCOMING')
        context = {
            'name': 'Mary',
            'visit_number': '2',
            'date': '15 May 2025',
            'facility': 'Kibera Health Centre',
        }
        rendered = sample_template.render_message(context)
        self.stdout.write(f'\n{rendered}\n')
        self.stdout.write('-'*70 + '\n')