# apps/delivery/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Delivery, Baby
from .forms import DeliveryForm, BabyForm
from apps.mothers.models import Pregnancy
from apps.users.views import _get_scoped_facilities


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _get_scoped_deliveries(user):
    """
    Scope deliveries to user's facility.
    Mirrors _get_scoped_anc / _get_scoped_facilities pattern.
    """
    qs = Delivery.objects.select_related(
        'pregnancy__mother',
        'pregnancy',
        'facility',
        'attended_by',
    )
    if user.role == 'MOH':
        return qs.all()
    return qs.filter(facility=user.facility)


def _get_scoped_pregnancies(user):
    """
    Return active pregnancies scoped to user's facility.
    Used to populate the pregnancy selector when recording a delivery.
    """
    qs = Pregnancy.objects.filter(status='ACTIVE').select_related('mother', 'facility')
    if user.role == 'MOH':
        return qs
    return qs.filter(facility=user.facility)


def _delivery_context(delivery):
    """Shared context for delivery detail and baby registration views."""
    return {
        'delivery':  delivery,
        'pregnancy': delivery.pregnancy,
        'mother':    delivery.pregnancy.mother,
        'babies':    delivery.babies.all(),
    }


# ─────────────────────────────────────────────
# Delivery Views
# ─────────────────────────────────────────────

@login_required
def delivery_list_view(request):
    """List deliveries scoped to user's role."""
    deliveries = _get_scoped_deliveries(request.user).order_by('-delivery_date')
    return render(request, 'delivery/delivery_list.html', {
        'deliveries': deliveries,
    })


@login_required
def delivery_detail_view(request, pk):
    """Read-only detail for a single delivery including its babies."""
    qs       = _get_scoped_deliveries(request.user)
    delivery = get_object_or_404(qs, pk=pk)
    return render(request, 'delivery/delivery_detail.html', _delivery_context(delivery))


@login_required
def delivery_create_view(request, pregnancy_pk):
    """
    Record a new delivery for an active pregnancy.
    URL carries pregnancy_pk so no pregnancy selector needed in the form.
    Guard: pregnancy must not already have a delivery recorded.
    """
    pregnancies = _get_scoped_pregnancies(request.user)
    pregnancy   = get_object_or_404(pregnancies, pk=pregnancy_pk)

    # Guard: one delivery per pregnancy (OneToOneField)
    if hasattr(pregnancy, 'delivery'):
        messages.info(request, "A delivery has already been recorded for this pregnancy.")
        return redirect('delivery:detail', pk=pregnancy.delivery.pk)

    form = DeliveryForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        delivery = form.save(
            pregnancy   = pregnancy,
            facility    = request.user.facility,
            attended_by = request.user,
        )
        messages.success(
            request,
            f"Delivery recorded for {pregnancy.mother.full_name}. "
            f"Please register the {'babies' if delivery.number_of_babies > 1 else 'baby'} below."
        )
        return redirect('delivery:register_baby', delivery_pk=delivery.pk)

    return render(request, 'delivery/delivery_form.html', {
        'form':      form,
        'pregnancy': pregnancy,
        'mother':    pregnancy.mother,
        'form_title': f'Record Delivery — {pregnancy.mother.full_name}',
    })


# ─────────────────────────────────────────────
# Baby Views
# ─────────────────────────────────────────────

@login_required
def baby_register_view(request, delivery_pk):
    """
    Register one or more babies after a delivery.
    Handles multiple babies via repeated POST submissions tracked by birth_order.
    """
    qs       = _get_scoped_deliveries(request.user)
    delivery = get_object_or_404(qs, pk=delivery_pk)
    mother   = delivery.pregnancy.mother

    registered_count  = delivery.babies.count()
    expected_count    = delivery.number_of_babies
    all_registered    = registered_count >= expected_count

    if all_registered:
        messages.info(request, "All babies for this delivery have been registered.")
        return redirect('delivery:detail', pk=delivery.pk)

    # Pre-set birth_order to the next unregistered baby
    initial = {
        'birth_order': registered_count + 1,
        'last_name':   mother.last_name,
    }

    form = BabyForm(request.POST or None, initial=initial)

    if request.method == 'POST' and form.is_valid():
        baby = form.save(
            delivery      = delivery,
            mother        = mother,
            facility      = request.user.facility,
            registered_by = request.user,
        )
        messages.success(
            request,
            f"{baby.display_name} registered successfully. "
            f"Immunization schedule auto-generated."
        )
        # If more babies expected, reload the same form for the next one
        if delivery.babies.count() < expected_count:
            return redirect('delivery:register_baby', delivery_pk=delivery.pk)
        return redirect('delivery:detail', pk=delivery.pk)

    return render(request, 'delivery/baby_form.html', {
        'form':             form,
        'delivery':         delivery,
        'mother':           mother,
        'registered_count': registered_count,
        'expected_count':   expected_count,
        'form_title':       f'Register Baby {registered_count + 1} of {expected_count}',
    })


@login_required
def baby_detail_view(request, pk):
    """Read-only detail for a single baby."""
    # scope via facility
    if request.user.role == 'MOH':
        baby = get_object_or_404(Baby, pk=pk)
    else:
        baby = get_object_or_404(Baby, pk=pk, facility=request.user.facility)

    return render(request, 'delivery/baby_detail.html', {
        'baby':           baby,
        'delivery':       baby.delivery,
        'mother':         baby.mother,
        'immunizations':  baby.immunization_schedules.select_related('vaccine').order_by('scheduled_date'),
    })