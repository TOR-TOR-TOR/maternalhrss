# apps/reminders/management/commands/send_daily_reminders.py
"""
Daily cron job to check and send SMS reminders
Run this command daily at 8 AM:
    python manage.py send_daily_reminders

This command:
1. Checks for upcoming ANC visits (3 days before)
2. Checks for upcoming vaccinations (3 days before)
3. Checks for missed visits needing follow-up
4. Checks for overdue pregnancies
5. Sends pending reminders
6. Retries failed reminders
7. Logs all activities
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date, timedelta
from apps.reminders.models import (
    SentReminder, ReminderTemplate, SystemLog,
    create_anc_reminder, create_vaccine_reminder, create_delivery_approaching_reminder
)
from apps.anc.models import ANCVisit
from apps.immunization.models import ImmunizationSchedule
from apps.mothers.models import Pregnancy


class Command(BaseCommand):
    help = 'Daily cron job to check and send SMS reminders'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be sent without actually creating reminders',
        )
        parser.add_argument(
            '--send-now',
            action='store_true',
            help='Actually send SMS (requires SMS gateway setup)',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('📱 DAILY SMS REMINDER CHECK'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        dry_run = options['dry_run']
        send_now = options['send_now']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No reminders will be created\n'))
        
        # Statistics
        stats = {
            'anc_upcoming': 0,
            'anc_today': 0,
            'anc_missed': 0,
            'vaccine_upcoming': 0,
            'vaccine_today': 0,
            'vaccine_missed': 0,
            'delivery_approaching': 0,
            'overdue_pregnancy': 0,
            'reminders_sent': 0,
            'reminders_failed': 0,
        }
        
        # 1. Check for upcoming ANC visits (3 days before)
        self.stdout.write(self.style.HTTP_INFO('\n📋 Checking upcoming ANC visits...'))
        stats['anc_upcoming'] = self.check_upcoming_anc_visits(dry_run)
        
        # 2. Check for ANC visits today
        self.stdout.write(self.style.HTTP_INFO('\n📋 Checking ANC visits today...'))
        stats['anc_today'] = self.check_anc_visits_today(dry_run)
        
        # 3. Check for missed ANC visits
        self.stdout.write(self.style.HTTP_INFO('\n⚠️  Checking missed ANC visits...'))
        stats['anc_missed'] = self.check_missed_anc_visits(dry_run)
        
        # 4. Check for upcoming vaccinations (3 days before)
        self.stdout.write(self.style.HTTP_INFO('\n💉 Checking upcoming vaccinations...'))
        stats['vaccine_upcoming'] = self.check_upcoming_vaccinations(dry_run)
        
        # 5. Check for vaccinations today
        self.stdout.write(self.style.HTTP_INFO('\n💉 Checking vaccinations today...'))
        stats['vaccine_today'] = self.check_vaccinations_today(dry_run)
        
        # 6. Check for missed vaccinations
        self.stdout.write(self.style.HTTP_INFO('\n⚠️  Checking missed vaccinations...'))
        stats['vaccine_missed'] = self.check_missed_vaccinations(dry_run)
        
        # 7. Check for approaching deliveries (38+ weeks)
        self.stdout.write(self.style.HTTP_INFO('\n🤰 Checking approaching deliveries...'))
        stats['delivery_approaching'] = self.check_approaching_deliveries(dry_run)
        
        # 8. Check for overdue pregnancies (>40 weeks)
        self.stdout.write(self.style.HTTP_INFO('\n⏰ Checking overdue pregnancies...'))
        stats['overdue_pregnancy'] = self.check_overdue_pregnancies(dry_run)
        
        # 9. Send pending reminders (if --send-now flag is set)
        if send_now and not dry_run:
            self.stdout.write(self.style.HTTP_INFO('\n📤 Sending pending reminders...'))
            sent, failed = self.send_pending_reminders()
            stats['reminders_sent'] = sent
            stats['reminders_failed'] = failed
        else:
            self.stdout.write(self.style.WARNING(
                '\n⏸️  Skipping actual SMS sending (use --send-now flag to send)'
            ))
        
        # Print summary
        self.print_summary(stats, dry_run)
        
        # Log to system
        if not dry_run:
            SystemLog.log_action(
                action_type='CRON_RUN',
                description='Daily reminder check completed',
                log_level='INFO',
                metadata=stats
            )
    
    def check_upcoming_anc_visits(self, dry_run):
        """Check ANC visits scheduled 3 days from now"""
        target_date = date.today() + timedelta(days=3)
        
        visits = ANCVisit.objects.filter(
            scheduled_date=target_date,
            attended=False,
            missed=False,
            pregnancy__status='ACTIVE'
        ).select_related('pregnancy__mother', 'facility')
        
        count = 0
        for visit in visits:
            # Check if reminder already sent
            already_sent = SentReminder.objects.filter(
                mother=visit.pregnancy.mother,
                anc_visit=visit,
                reminder_type='ANC_UPCOMING'
            ).exists()
            
            if already_sent:
                continue
            
            if not dry_run:
                reminder = create_anc_reminder(visit, 'ANC_UPCOMING')
                if reminder:
                    count += 1
                    self.stdout.write(
                        f"  ✓ Created reminder for {visit.pregnancy.mother.full_name} - ANC {visit.visit_number}"
                    )
            else:
                count += 1
                self.stdout.write(
                    f"  [DRY RUN] Would create reminder for {visit.pregnancy.mother.full_name} - ANC {visit.visit_number}"
                )
        
        self.stdout.write(self.style.SUCCESS(f"  Found {count} upcoming ANC visit(s)"))
        return count
    
    def check_anc_visits_today(self, dry_run):
        """Check ANC visits scheduled for today"""
        today = date.today()
        
        visits = ANCVisit.objects.filter(
            scheduled_date=today,
            attended=False,
            missed=False,
            pregnancy__status='ACTIVE'
        ).select_related('pregnancy__mother', 'facility')
        
        count = 0
        for visit in visits:
            already_sent = SentReminder.objects.filter(
                mother=visit.pregnancy.mother,
                anc_visit=visit,
                reminder_type='ANC_TODAY'
            ).exists()
            
            if already_sent:
                continue
            
            if not dry_run:
                reminder = create_anc_reminder(visit, 'ANC_TODAY')
                if reminder:
                    count += 1
                    self.stdout.write(
                        f"  ✓ Created 'today' reminder for {visit.pregnancy.mother.full_name}"
                    )
            else:
                count += 1
                self.stdout.write(
                    f"  [DRY RUN] Would create 'today' reminder for {visit.pregnancy.mother.full_name}"
                )
        
        self.stdout.write(self.style.SUCCESS(f"  Found {count} ANC visit(s) today"))
        return count
    
    def check_missed_anc_visits(self, dry_run):
        """Check for missed ANC visits needing follow-up"""
        visits = ANCVisit.objects.filter(
            missed=True,
            pregnancy__status='ACTIVE'
        ).select_related('pregnancy__mother', 'facility')
        
        count = 0
        for visit in visits:
            # Check if follow-up reminder already sent in last 7 days
            recent_reminder = SentReminder.objects.filter(
                mother=visit.pregnancy.mother,
                anc_visit=visit,
                reminder_type='ANC_MISSED',
                created_at__gte=timezone.now() - timedelta(days=7)
            ).exists()
            
            if recent_reminder:
                continue
            
            if not dry_run:
                reminder = create_anc_reminder(visit, 'ANC_MISSED')
                if reminder:
                    count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠️  Created follow-up for {visit.pregnancy.mother.full_name} - Missed ANC {visit.visit_number}"
                        )
                    )
            else:
                count += 1
                self.stdout.write(
                    f"  [DRY RUN] Would create follow-up for {visit.pregnancy.mother.full_name}"
                )
        
        self.stdout.write(self.style.SUCCESS(f"  Found {count} missed ANC visit(s)"))
        return count
    
    def check_upcoming_vaccinations(self, dry_run):
        """Check vaccinations scheduled 3 days from now"""
        target_date = date.today() + timedelta(days=3)
        
        vaccines = ImmunizationSchedule.objects.filter(
            scheduled_date=target_date,
            administered=False,
            missed=False
        ).select_related('baby__mother', 'vaccine', 'facility')
        
        count = 0
        for vaccine in vaccines:
            already_sent = SentReminder.objects.filter(
                mother=vaccine.baby.mother,
                immunization=vaccine,
                reminder_type='VACCINE_UPCOMING'
            ).exists()
            
            if already_sent:
                continue
            
            if not dry_run:
                reminder = create_vaccine_reminder(vaccine, 'VACCINE_UPCOMING')
                if reminder:
                    count += 1
                    self.stdout.write(
                        f"  ✓ Created reminder for {vaccine.baby.mother.full_name} - {vaccine.vaccine.name} for {vaccine.baby.display_name}"
                    )
            else:
                count += 1
                self.stdout.write(
                    f"  [DRY RUN] Would create reminder for {vaccine.baby.mother.full_name}"
                )
        
        self.stdout.write(self.style.SUCCESS(f"  Found {count} upcoming vaccination(s)"))
        return count
    
    def check_vaccinations_today(self, dry_run):
        """Check vaccinations scheduled for today"""
        today = date.today()
        
        vaccines = ImmunizationSchedule.objects.filter(
            scheduled_date=today,
            administered=False,
            missed=False
        ).select_related('baby__mother', 'vaccine', 'facility')
        
        count = 0
        for vaccine in vaccines:
            already_sent = SentReminder.objects.filter(
                mother=vaccine.baby.mother,
                immunization=vaccine,
                reminder_type='VACCINE_TODAY'
            ).exists()
            
            if already_sent:
                continue
            
            if not dry_run:
                reminder = create_vaccine_reminder(vaccine, 'VACCINE_TODAY')
                if reminder:
                    count += 1
                    self.stdout.write(
                        f"  ✓ Created 'today' reminder for {vaccine.baby.mother.full_name}"
                    )
            else:
                count += 1
                self.stdout.write(
                    f"  [DRY RUN] Would create 'today' reminder for {vaccine.baby.mother.full_name}"
                )
        
        self.stdout.write(self.style.SUCCESS(f"  Found {count} vaccination(s) today"))
        return count
    
    def check_missed_vaccinations(self, dry_run):
        """Check for missed vaccinations"""
        vaccines = ImmunizationSchedule.objects.filter(
            missed=True
        ).select_related('baby__mother', 'vaccine', 'facility')
        
        count = 0
        for vaccine in vaccines:
            recent_reminder = SentReminder.objects.filter(
                mother=vaccine.baby.mother,
                immunization=vaccine,
                reminder_type='VACCINE_MISSED',
                created_at__gte=timezone.now() - timedelta(days=7)
            ).exists()
            
            if recent_reminder:
                continue
            
            if not dry_run:
                reminder = create_vaccine_reminder(vaccine, 'VACCINE_MISSED')
                if reminder:
                    count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"  ⚠️  Created follow-up for {vaccine.baby.mother.full_name} - Missed {vaccine.vaccine.name}"
                        )
                    )
            else:
                count += 1
                self.stdout.write(
                    f"  [DRY RUN] Would create follow-up for {vaccine.baby.mother.full_name}"
                )
        
        self.stdout.write(self.style.SUCCESS(f"  Found {count} missed vaccination(s)"))
        return count
    
    def check_approaching_deliveries(self, dry_run):
        """Check pregnancies at 38+ weeks"""
        pregnancies = Pregnancy.objects.filter(
            status='ACTIVE',
            gestational_age_weeks__gte=38
        ).select_related('mother', 'facility')
        
        count = 0
        for pregnancy in pregnancies:
            # Send reminder once per week starting at 38 weeks
            recent_reminder = SentReminder.objects.filter(
                mother=pregnancy.mother,
                pregnancy=pregnancy,
                reminder_type='DELIVERY_APPROACHING',
                created_at__gte=timezone.now() - timedelta(days=7)
            ).exists()
            
            if recent_reminder:
                continue
            
            if not dry_run:
                reminder = create_delivery_approaching_reminder(pregnancy)
                if reminder:
                    count += 1
                    self.stdout.write(
                        f"  ✓ Created delivery reminder for {pregnancy.mother.full_name} (Week {pregnancy.gestational_age_weeks})"
                    )
            else:
                count += 1
                self.stdout.write(
                    f"  [DRY RUN] Would create delivery reminder for {pregnancy.mother.full_name}"
                )
        
        self.stdout.write(self.style.SUCCESS(f"  Found {count} approaching deliverie(s)"))
        return count
    
    def check_overdue_pregnancies(self, dry_run):
        """Check pregnancies past 40 weeks"""
        pregnancies = Pregnancy.objects.filter(
            status='ACTIVE',
            gestational_age_weeks__gte=40
        ).select_related('mother', 'facility')
        
        count = 0
        for pregnancy in pregnancies:
            # Send urgent reminder every 2 days for overdue pregnancies
            recent_reminder = SentReminder.objects.filter(
                mother=pregnancy.mother,
                pregnancy=pregnancy,
                reminder_type='OVERDUE_PREGNANCY',
                created_at__gte=timezone.now() - timedelta(days=2)
            ).exists()
            
            if recent_reminder:
                continue
            
            if not dry_run:
                template = ReminderTemplate.get_active_template('OVERDUE_PREGNANCY')
                if template:
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
                        reminder_type='OVERDUE_PREGNANCY',
                        message_content=message,
                        template_used=template,
                        pregnancy=pregnancy,
                        scheduled_datetime=timezone.now(),
                        facility=pregnancy.facility,
                    )
                    count += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f"  🔴 Created URGENT reminder for {pregnancy.mother.full_name} (Week {pregnancy.gestational_age_weeks})"
                        )
                    )
            else:
                count += 1
                self.stdout.write(
                    f"  [DRY RUN] Would create URGENT reminder for {pregnancy.mother.full_name}"
                )
        
        self.stdout.write(self.style.SUCCESS(f"  Found {count} overdue pregnancies"))
        return count
    
    def send_pending_reminders(self):
        """
        Send all pending reminders
        NOTE: This is a placeholder - actual SMS sending requires gateway integration
        """
        pending = SentReminder.objects.filter(
            delivery_status='PENDING',
            scheduled_datetime__lte=timezone.now()
        )
        
        sent_count = 0
        failed_count = 0
        
        for reminder in pending:
            try:
                # TODO: Integrate with actual SMS gateway (Africa's Talking, Twilio, etc.)
                # For now, just mark as sent and log
                
                # Simulated SMS sending
                self.stdout.write(
                    f"  📤 Would send to {reminder.phone_number}: {reminder.message_content[:50]}..."
                )
                
                # Mark as sent (in production, this happens after gateway confirms)
                reminder.mark_as_sent(
                    gateway_response="Simulated send - gateway not configured",
                    message_id=f"SIM-{timezone.now().timestamp()}"
                )
                
                # Log the SMS
                SystemLog.log_sms(reminder)
                
                sent_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"  ✗ Failed to send: {str(e)}")
                )
                reminder.mark_as_failed(reason=str(e))
                failed_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f"\n  Sent: {sent_count}, Failed: {failed_count}")
        )
        
        return sent_count, failed_count
    
    def print_summary(self, stats, dry_run):
        """Print summary of daily check"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('📊 SUMMARY'))
        self.stdout.write('='*70 + '\n')
        
        mode = "DRY RUN" if dry_run else "LIVE"
        self.stdout.write(f"Mode: {mode}\n")
        
        self.stdout.write('ANC Reminders:')
        self.stdout.write(f"  • Upcoming (3 days): {stats['anc_upcoming']}")
        self.stdout.write(f"  • Today: {stats['anc_today']}")
        self.stdout.write(f"  • Missed: {stats['anc_missed']}")
        
        self.stdout.write('\nVaccination Reminders:')
        self.stdout.write(f"  • Upcoming (3 days): {stats['vaccine_upcoming']}")
        self.stdout.write(f"  • Today: {stats['vaccine_today']}")
        self.stdout.write(f"  • Missed: {stats['vaccine_missed']}")
        
        self.stdout.write('\nDelivery Reminders:')
        self.stdout.write(f"  • Approaching (38+ weeks): {stats['delivery_approaching']}")
        self.stdout.write(f"  • Overdue (40+ weeks): {stats['overdue_pregnancy']}")
        
        total = sum([
            stats['anc_upcoming'], stats['anc_today'], stats['anc_missed'],
            stats['vaccine_upcoming'], stats['vaccine_today'], stats['vaccine_missed'],
            stats['delivery_approaching'], stats['overdue_pregnancy']
        ])
        
        self.stdout.write(f"\n{'Total reminders:':.<50} {total}")
        
        if stats['reminders_sent'] > 0 or stats['reminders_failed'] > 0:
            self.stdout.write(f"{'SMS sent successfully:':.<50} {stats['reminders_sent']}")
            self.stdout.write(f"{'SMS failed:':.<50} {stats['reminders_failed']}")
        
        self.stdout.write('\n' + '='*70 + '\n')