# apps/immunization/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date

from .models import ImmunizationSchedule
from .forms import ImmunizationRecordForm


# ─────────────────────────────────────────────
# Constants — mirrors pattern in anc/views.py
# ─────────────────────────────────────────────

FILTER_TABS = [
    ('upcoming',     'Upcoming',     'green'),
    ('overdue',      'Overdue',      'amber'),
    ('missed',       'Missed',       'red'),
    ('administered', 'Administered', 'gray'),
]


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _get_scoped_immunizations(user):
    """
    Scope ImmunizationSchedule queryset to user's facility.
    Mirrors the _get_scoped_* pattern used across all apps.
    """
    qs = ImmunizationSchedule.objects.select_related(
        'baby__mother',
        'baby__delivery',
        'vaccine',
        'facility',
        'administered_by',
    )
    if user.role == 'MOH':
        return qs.all()
    return qs.filter(facility=user.facility)


def _schedule_context(schedule):
    """Shared context dict for detail, record, and update views."""
    return {
        'schedule': schedule,
        'baby':     schedule.baby,
        'mother':   schedule.baby.mother,
        'vaccine':  schedule.vaccine,
    }


# ─────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────

@login_required
def immunization_list_view(request):
    """
    List immunization schedules scoped to user's facility.
    Supports ?status= filter.
    """
    qs     = _get_scoped_immunizations(request.user)
    status = request.GET.get('status', '')
    today  = date.today()

    filter_map = {
        'upcoming':     dict(scheduled_date__gte=today,
                             administered=False, missed=False),
        'overdue':      dict(scheduled_date__lt=today,
                             administered=False, missed=False),
        'administered': dict(administered=True),
        'missed':       dict(missed=True),
    }

    if status in filter_map:
        qs = qs.filter(**filter_map[status])

    return render(request, 'immunization/immunization_list.html', {
        'schedules':     qs.order_by('scheduled_date'),
        'active_filter': status,
        'filters':       FILTER_TABS,
    })


@login_required
def immunization_detail_view(request, pk):
    """Read-only detail view for a single immunization schedule entry."""
    qs       = _get_scoped_immunizations(request.user)
    schedule = get_object_or_404(qs, pk=pk)
    return render(request, 'immunization/immunization_detail.html',
                  _schedule_context(schedule))


@login_required
def immunization_record_view(request, pk):
    """
    Record administration of a scheduled vaccine.
    Guard: cannot re-record an already administered vaccine.
    """
    qs       = _get_scoped_immunizations(request.user)
    schedule = get_object_or_404(qs, pk=pk)

    if schedule.administered:
        messages.info(request, "This vaccine has already been recorded as administered.")
        return redirect('immunization:detail', pk=schedule.pk)

    form = ImmunizationRecordForm(request.POST or None, instance=schedule)

    if request.method == 'POST' and form.is_valid():
        form.save(
            administered_by = request.user,
            facility        = request.user.facility,
        )
        messages.success(
            request,
            f"{schedule.vaccine.name} administered to "
            f"{schedule.baby.display_name} successfully."
        )
        return redirect('immunization:detail', pk=schedule.pk)

    return render(request, 'immunization/immunization_record.html', {
        **_schedule_context(schedule),
        'form': form,
    })


@login_required
def immunization_update_view(request, pk):
    """
    Edit an already-recorded immunization entry.
    Nurses can only edit records they administered.
    """
    qs       = _get_scoped_immunizations(request.user)
    schedule = get_object_or_404(qs, pk=pk, administered=True)

    if request.user.role == 'NURSE' and schedule.administered_by != request.user:
        messages.error(request, "You can only edit vaccines you administered.")
        return redirect('immunization:detail', pk=schedule.pk)

    form = ImmunizationRecordForm(request.POST or None, instance=schedule)

    if request.method == 'POST' and form.is_valid():
        form.save(
            administered_by = schedule.administered_by,
            facility        = schedule.facility,
        )
        messages.success(request, "Immunization record updated successfully.")
        return redirect('immunization:detail', pk=schedule.pk)

    return render(request, 'immunization/immunization_record.html', {
        **_schedule_context(schedule),
        'form':      form,
        'is_update': True,
    })