# apps/reminders/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import SentReminder, ReminderTemplate
from apps.reminders.models import (
    create_anc_reminder,
    create_vaccine_reminder,
    create_delivery_approaching_reminder,
)
from apps.anc.models import ANCVisit
from apps.immunization.models import ImmunizationSchedule
from apps.mothers.models import Pregnancy


# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

TEMPLATE_PLACEHOLDERS = [
    ('{name}',           "Mother's first name"),
    ('{visit_number}',   'ANC visit number'),
    ('{date}',           'Appointment date'),
    ('{time}',           'Appointment time'),
    ('{facility}',       'Facility name'),
    ('{vaccine_name}',   'Vaccine name'),
    ('{baby_name}',      "Baby's name"),
    ('{weeks_pregnant}', 'Gestational age'),
    ('{edd}',            'Expected due date'),
]


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _get_scoped_reminders(user):
    """
    Scope SentReminder queryset to user's facility.
    Mirrors the _get_scoped_* pattern used across all apps.
    """
    qs = SentReminder.objects.select_related(
        'mother', 'facility', 'template_used',
        'anc_visit', 'baby', 'immunization', 'pregnancy',
    )
    if user.role == 'MOH':
        return qs.all()
    return qs.filter(facility=user.facility)


# ─────────────────────────────────────────────
# SMS Log Views
# ─────────────────────────────────────────────

@login_required
def reminder_list_view(request):
    """
    List all sent reminders scoped to user's facility.
    Supports ?status= and ?type= filters.
    """
    qs            = _get_scoped_reminders(request.user)
    status_filter = request.GET.get('status', '')
    type_filter   = request.GET.get('type', '')

    if status_filter:
        qs = qs.filter(delivery_status=status_filter)
    if type_filter:
        qs = qs.filter(reminder_type=type_filter)

    return render(request, 'reminders/reminder_list.html', {
        'reminders':      qs.order_by('-scheduled_datetime'),
        'status_filter':  status_filter,
        'type_filter':    type_filter,
        'status_choices': SentReminder.DELIVERY_STATUS,
        'type_choices':   SentReminder.REMINDER_TYPES,
    })


@login_required
def reminder_detail_view(request, pk):
    """Read-only detail view for a single sent reminder."""
    qs       = _get_scoped_reminders(request.user)
    reminder = get_object_or_404(qs, pk=pk)
    return render(request, 'reminders/reminder_detail.html', {
        'reminder': reminder,
    })


# ─────────────────────────────────────────────
# Manual Reminder Triggers
# ─────────────────────────────────────────────

@login_required
def send_anc_reminder_view(request, anc_visit_pk):
    """Manually trigger an ANC reminder for a specific visit."""
    if request.user.role == 'MOH':
        visit = get_object_or_404(ANCVisit, pk=anc_visit_pk)
    else:
        visit = get_object_or_404(ANCVisit, pk=anc_visit_pk,
                                  facility=request.user.facility)

    if request.method == 'POST':
        reminder_type = request.POST.get('reminder_type', 'ANC_UPCOMING')
        reminder = create_anc_reminder(visit, reminder_type=reminder_type)

        if reminder:
            reminder.is_manual = True
            reminder.sent_by   = request.user
            reminder.save(update_fields=['is_manual', 'sent_by'])
            messages.success(
                request,
                f"Reminder queued for {visit.pregnancy.mother.full_name} "
                f"— ANC Visit {visit.visit_number}."
            )
        else:
            messages.error(request, "No active template found for this reminder type.")

        return redirect('anc:detail', pk=visit.pk)

    return render(request, 'reminders/confirm_send.html', {
        'context_label':  f"ANC Visit {visit.visit_number} — {visit.pregnancy.mother.full_name}",
        'scheduled_date': visit.scheduled_date,
        'phone_number':   visit.pregnancy.mother.phone_number,
        'action_url':     request.path,
        'reminder_types': [
            ('ANC_UPCOMING', 'Upcoming Reminder (3 days before)'),
            ('ANC_TODAY',    'Same-Day Reminder'),
            ('ANC_MISSED',   'Missed Visit Follow-up'),
        ],
    })


@login_required
def send_vaccine_reminder_view(request, immunization_pk):
    """Manually trigger a vaccine reminder for a specific immunization schedule."""
    if request.user.role == 'MOH':
        immunization = get_object_or_404(ImmunizationSchedule, pk=immunization_pk)
    else:
        immunization = get_object_or_404(ImmunizationSchedule, pk=immunization_pk,
                                         facility=request.user.facility)

    if request.method == 'POST':
        reminder_type = request.POST.get('reminder_type', 'VACCINE_UPCOMING')
        reminder = create_vaccine_reminder(immunization, reminder_type=reminder_type)

        if reminder:
            reminder.is_manual = True
            reminder.sent_by   = request.user
            reminder.save(update_fields=['is_manual', 'sent_by'])
            messages.success(
                request,
                f"Reminder queued for {immunization.baby.mother.full_name} "
                f"— {immunization.vaccine.name}."
            )
        else:
            messages.error(request, "No active template found for this reminder type.")

        return redirect('immunization:detail', pk=immunization.pk)

    return render(request, 'reminders/confirm_send.html', {
        'context_label':  f"{immunization.vaccine.name} — {immunization.baby.display_name}",
        'scheduled_date': immunization.scheduled_date,
        'phone_number':   immunization.baby.mother.phone_number,
        'action_url':     request.path,
        'reminder_types': [
            ('VACCINE_UPCOMING', 'Upcoming Reminder (3 days before)'),
            ('VACCINE_TODAY',    'Same-Day Reminder'),
            ('VACCINE_MISSED',   'Missed Vaccine Follow-up'),
        ],
    })


@login_required
def send_delivery_reminder_view(request, pregnancy_pk):
    """Manually trigger a delivery-approaching reminder for a pregnancy."""
    if request.user.role == 'MOH':
        pregnancy = get_object_or_404(Pregnancy, pk=pregnancy_pk, status='ACTIVE')
    else:
        pregnancy = get_object_or_404(Pregnancy, pk=pregnancy_pk,
                                      status='ACTIVE',
                                      facility=request.user.facility)

    if request.method == 'POST':
        reminder = create_delivery_approaching_reminder(pregnancy)

        if reminder:
            reminder.is_manual = True
            reminder.sent_by   = request.user
            reminder.save(update_fields=['is_manual', 'sent_by'])
            messages.success(
                request,
                f"Delivery reminder queued for {pregnancy.mother.full_name}."
            )
        else:
            messages.error(request, "No active template found for delivery reminders.")

        return redirect('mothers:pregnancy_detail', pk=pregnancy.pk)

    return render(request, 'reminders/confirm_send.html', {
        'context_label':  f"Delivery Approaching — {pregnancy.mother.full_name}",
        'scheduled_date': pregnancy.edd,
        'phone_number':   pregnancy.mother.phone_number,
        'action_url':     request.path,
        'reminder_types': [
            ('DELIVERY_APPROACHING', 'Delivery Approaching (2 weeks)'),
        ],
    })


# ─────────────────────────────────────────────
# Template Management (Manager + MOH only)
# ─────────────────────────────────────────────

@login_required
def template_list_view(request):
    """List all SMS templates. Manager/MOH only."""
    if request.user.role == 'NURSE':
        messages.error(request, "You do not have permission to manage SMS templates.")
        return redirect('users:nurse_dashboard')

    templates = ReminderTemplate.objects.all().order_by('reminder_type')
    return render(request, 'reminders/template_list.html', {
        'templates': templates,
    })


@login_required
def template_detail_view(request, pk):
    """View a single SMS template with placeholder reference."""
    if request.user.role == 'NURSE':
        messages.error(request, "You do not have permission to view SMS templates.")
        return redirect('users:nurse_dashboard')

    template = get_object_or_404(ReminderTemplate, pk=pk)
    return render(request, 'reminders/template_detail.html', {
        'template':     template,
        'sent_count':   template.sent_reminders.count(),
        'placeholders': TEMPLATE_PLACEHOLDERS,
    })