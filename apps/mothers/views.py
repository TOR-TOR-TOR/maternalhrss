# apps/mothers/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Mother, Pregnancy
from .forms import MotherRegistrationForm, MotherUpdateForm, PregnancyForm
from apps.users.views import role_required


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _get_scoped_mothers(user):
    """
    Scope Mother queryset to user's facility.
    Mirrors the _get_scoped_* pattern used across all apps.
    """
    qs = Mother.objects.select_related('facility', 'registered_by')
    if user.role == 'MOH':
        return qs.all()
    return qs.filter(facility=user.facility)


def _get_scoped_pregnancies(user):
    """
    Scope Pregnancy queryset to user's facility.
    """
    qs = Pregnancy.objects.select_related('mother', 'facility', 'registered_by')
    if user.role == 'MOH':
        return qs.all()
    return qs.filter(facility=user.facility)


def _mother_context(mother):
    """
    Shared context for mother detail, update and pregnancy views.
    Preloads related data used across multiple templates.
    """
    active_pregnancy = mother.active_pregnancy
    return {
        'mother':           mother,
        'active_pregnancy': active_pregnancy,
        'pregnancies':      mother.pregnancies.order_by('-registration_date'),
        'babies':           mother.babies.select_related('delivery').order_by(
                                '-delivery__delivery_date'
                            ),
    }


# ─────────────────────────────────────────────
# Mother Views
# ─────────────────────────────────────────────

@login_required
def mother_list_view(request):
    """
    List mothers scoped to user's facility.
    Supports ?q= search by name or phone number.
    """
    qs    = _get_scoped_mothers(request.user)
    query = request.GET.get('q', '').strip()

    if query:
        qs = qs.filter(
            # Search by first name, last name, or phone — OR across all three
            first_name__icontains=query
        ) | _get_scoped_mothers(request.user).filter(
            last_name__icontains=query
        ) | _get_scoped_mothers(request.user).filter(
            phone_number__icontains=query
        )

    return render(request, 'mothers/mother_list.html', {
        'mothers': qs.order_by('-registration_date'),
        'query':   query,
    })


@login_required
def mother_detail_view(request, pk):
    """Full detail view for a mother — includes pregnancies, babies, ANC summary."""
    qs     = _get_scoped_mothers(request.user)
    mother = get_object_or_404(qs, pk=pk)
    return render(request, 'mothers/mother_detail.html', _mother_context(mother))


@login_required
def mother_register_view(request):
    """Register a new mother at the nurse's facility."""
    form = MotherRegistrationForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        mother = form.save(
            facility      = request.user.facility,
            registered_by = request.user,
        )
        messages.success(
            request,
            f"{mother.full_name} registered successfully. "
            f"You can now register her pregnancy."
        )
        return redirect('mothers:register_pregnancy', mother_pk=mother.pk)

    return render(request, 'mothers/mother_form.html', {
        'form':       form,
        'form_title': 'Register New Mother',
    })


@login_required
def mother_update_view(request, pk):
    """Update an existing mother's details."""
    qs     = _get_scoped_mothers(request.user)
    mother = get_object_or_404(qs, pk=pk)
    form   = MotherUpdateForm(request.POST or None, instance=mother)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"{mother.full_name}'s record updated successfully.")
        return redirect('mothers:detail', pk=mother.pk)

    return render(request, 'mothers/mother_form.html', {
        'form':       form,
        'form_title': f'Edit {mother.full_name}',
        'mother':     mother,
    })


# ─────────────────────────────────────────────
# Pregnancy Views
# ─────────────────────────────────────────────

@login_required
def pregnancy_register_view(request, mother_pk):
    """
    Register a new pregnancy for an existing mother.
    URL carries mother_pk — no mother selector in the form.
    Guard: mother cannot have two active pregnancies simultaneously.
    """
    qs     = _get_scoped_mothers(request.user)
    mother = get_object_or_404(qs, pk=mother_pk)

    # Guard: one active pregnancy at a time
    if mother.has_active_pregnancy:
        messages.warning(
            request,
            f"{mother.full_name} already has an active pregnancy. "
            f"Complete or close it before registering a new one."
        )
        return redirect('mothers:detail', pk=mother.pk)

    form = PregnancyForm(request.POST or None, mother=mother)

    if request.method == 'POST' and form.is_valid():
        pregnancy = form.save(
            mother        = mother,
            facility      = request.user.facility,
            registered_by = request.user,
        )
        messages.success(
            request,
            f"Pregnancy registered for {mother.full_name}. "
            f"EDD: {pregnancy.edd.strftime('%d %b %Y')}. "
            f"8 ANC contacts auto-generated."
        )
        return redirect('mothers:pregnancy_detail', pk=pregnancy.pk)

    return render(request, 'mothers/pregnancy_form.html', {
        'form':       form,
        'mother':     mother,
        'form_title': f'Register Pregnancy — {mother.full_name}',
    })


@login_required
def pregnancy_detail_view(request, pk):
    """
    Full pregnancy detail — includes ANC visit schedule and delivery status.
    """
    qs        = _get_scoped_pregnancies(request.user)
    pregnancy = get_object_or_404(qs, pk=pk)

    anc_visits = pregnancy.anc_visits.order_by('visit_number').select_related(
        'recorded_by'
    )

    return render(request, 'mothers/pregnancy_detail.html', {
        'pregnancy':  pregnancy,
        'mother':     pregnancy.mother,
        'anc_visits': anc_visits,
        'delivery':   getattr(pregnancy, 'delivery', None),
    })


@login_required
def pregnancy_update_view(request, pk):
    """
    Update pregnancy details — risk level, notes, obstetric history.
    Status updates (DELIVERED, MISCARRIAGE etc.) happen via delivery recording,
    not this form — so status field is excluded.
    """
    qs        = _get_scoped_pregnancies(request.user)
    pregnancy = get_object_or_404(qs, pk=pk)
    form      = PregnancyForm(
        request.POST or None,
        instance=pregnancy,
        mother=pregnancy.mother,
    )

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Pregnancy record updated successfully.")
        return redirect('mothers:pregnancy_detail', pk=pregnancy.pk)

    return render(request, 'mothers/pregnancy_form.html', {
        'form':       form,
        'mother':     pregnancy.mother,
        'pregnancy':  pregnancy,
        'form_title': f'Edit Pregnancy — {pregnancy.mother.full_name}',
        'is_update':  True,
    })