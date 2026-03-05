# apps/anc/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import date

from .models import ANCVisit
from .forms import ANCVisitRecordForm


# ─────────────────────────────────────────────
# Constants — single source of truth for
# filter tabs and intervention labels used
# across list and detail templates.
# ─────────────────────────────────────────────

FILTER_TABS = [
    ('upcoming', 'Upcoming',  'green'),
    ('overdue',  'Overdue',   'amber'),
    ('missed',   'Missed',    'red'),
    ('attended', 'Attended',  'gray'),
]

INTERVENTION_LABELS = [
    ('iron_given',           'Iron Supplement'),
    ('folic_acid_given',     'Folic Acid'),
    ('deworming_done',       'Deworming'),
    ('tetanus_vaccine_given','TT Vaccine'),
]

SUPPLEMENT_FIELDS = [
    ('iron_given',            'Iron Supplement'),
    ('folic_acid_given',      'Folic Acid'),
    ('deworming_done',        'Deworming'),
    ('tetanus_vaccine_given', 'TT Vaccine'),
]


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _get_scoped_anc(user):
    """
    Return ANCVisit queryset scoped to the user's facility.
    MOH sees all; MANAGER and NURSE see only their facility.
    """
    qs = ANCVisit.objects.select_related(
        'pregnancy__mother',
        'pregnancy',
        'facility',
        'recorded_by',
    )
    if user.role == 'MOH':
        return qs.all()
    return qs.filter(facility=user.facility)


def _visit_context(visit):
    """Shared context dict used by detail, record, and update views."""
    return {
        'visit':      visit,
        'mother':     visit.pregnancy.mother,
        'pregnancy':  visit.pregnancy,
    }


# ─────────────────────────────────────────────
# Views
# ─────────────────────────────────────────────

@login_required
def anc_list_view(request):
    """
    List ANC visits scoped to the user's role.
    Supports ?status= filter.
    """
    qs     = _get_scoped_anc(request.user)
    status = request.GET.get('status', '')
    today  = date.today()

    filter_map = {
        'attended': dict(attended=True),
        'missed':   dict(missed=True),
        'overdue':  dict(
                        scheduled_date__lt=today,
                        attended=False,
                        missed=False,
                        pregnancy__status='ACTIVE',
                    ),
        'upcoming': dict(
                        scheduled_date__gte=today,
                        attended=False,
                        missed=False,
                        pregnancy__status='ACTIVE',
                    ),
    }

    if status in filter_map:
        qs = qs.filter(**filter_map[status])

    return render(request, 'anc/anc_list.html', {
        'visits':        qs.order_by('scheduled_date'),
        'active_filter': status,
        'filters':       FILTER_TABS,
        'today':         today,
    })


@login_required
def anc_detail_view(request, pk):
    """Read-only detail for a single ANC visit."""
    qs    = _get_scoped_anc(request.user)
    visit = get_object_or_404(qs, pk=pk)

    # Build interventions list for template — avoids logic in template
    interventions = [
        (label, getattr(visit, field))
        for field, label in INTERVENTION_LABELS
    ]

    return render(request, 'anc/anc_detail.html', {
        **_visit_context(visit),
        'interventions':   interventions,
    })


@login_required
def anc_record_view(request, pk):
    """
    Record clinical data for an existing ANC visit.
    Only for visits not yet attended.
    """
    qs    = _get_scoped_anc(request.user)
    visit = get_object_or_404(qs, pk=pk)

    if visit.attended:
        messages.info(request, "This visit has already been recorded.")
        return redirect('anc:detail', pk=visit.pk)

    form = ANCVisitRecordForm(request.POST or None, instance=visit)

    if request.method == 'POST' and form.is_valid():
        form.save(recorded_by=request.user)
        messages.success(
            request,
            f"ANC Visit {visit.visit_number} for "
            f"{visit.pregnancy.mother.full_name} recorded successfully."
        )
        return redirect('anc:detail', pk=visit.pk)

    return render(request, 'anc/anc_record.html', {
        **_visit_context(visit),
        'form':             form,
        'supplement_fields': SUPPLEMENT_FIELDS,
    })


@login_required
def anc_update_view(request, pk):
    """
    Edit an already-recorded ANC visit.
    Nurses can only edit visits they recorded.
    """
    qs    = _get_scoped_anc(request.user)
    visit = get_object_or_404(qs, pk=pk, attended=True)

    if request.user.role == 'NURSE' and visit.recorded_by != request.user:
        messages.error(request, "You can only edit visits you recorded.")
        return redirect('anc:detail', pk=visit.pk)

    form = ANCVisitRecordForm(request.POST or None, instance=visit)

    if request.method == 'POST' and form.is_valid():
        form.save(recorded_by=visit.recorded_by)
        messages.success(request, "ANC visit updated successfully.")
        return redirect('anc:detail', pk=visit.pk)

    return render(request, 'anc/anc_record.html', {
        **_visit_context(visit),
        'form':              form,
        'supplement_fields': SUPPLEMENT_FIELDS,
        'is_update':         True,
    })