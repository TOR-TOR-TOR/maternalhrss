# apps/anc/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from .models import ANCVisit
from apps.mothers.models import Mother, Pregnancy
from .forms import ANCVisitForm  # You'll need to create this form


@login_required
def anc_visit_list(request):
    """
    List all ANC visits for the nurse's facility with filtering options.
    """
    facility = request.user.facility
    today = timezone.now().date()
    
    # Base queryset
    visits = ANCVisit.objects.filter(
        pregnancy__mother__facility=facility
    ).select_related('pregnancy__mother', 'recorded_by').order_by('-scheduled_date')
    
    # Filter by status
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'today':
        visits = visits.filter(scheduled_date=today, attended=False)
    elif status_filter == 'upcoming':
        visits = visits.filter(scheduled_date__gt=today, attended=False, missed=False)
    elif status_filter == 'overdue':
        visits = visits.filter(scheduled_date__lt=today, attended=False, missed=False)
    elif status_filter == 'completed':
        visits = visits.filter(attended=True)
    elif status_filter == 'missed':
        visits = visits.filter(missed=True)
    
    # Filter by risk level
    risk_filter = request.GET.get('risk', '')
    if risk_filter:
        visits = visits.filter(pregnancy__risk_level=risk_filter)
    
    # Search by mother name or ID
    search_query = request.GET.get('search', '')
    if search_query:
        visits = visits.filter(
            Q(pregnancy__mother__first_name__icontains=search_query) |
            Q(pregnancy__mother__last_name__icontains=search_query) |
            Q(pregnancy__mother__mother_id__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(visits, 25)  # 25 visits per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Statistics
    stats = {
        'today': visits.filter(scheduled_date=today, attended=False).count(),
        'upcoming': visits.filter(scheduled_date__gt=today, attended=False, missed=False).count(),
        'overdue': visits.filter(scheduled_date__lt=today, attended=False, missed=False).count(),
        'completed': visits.filter(attended=True).count(),
    }
    
    context = {
        'page_title': 'ANC Visits',
        'visits': page_obj,
        'stats': stats,
        'status_filter': status_filter,
        'risk_filter': risk_filter,
        'search_query': search_query,
    }
    return render(request, 'anc/visit_list.html', context)


@login_required
def anc_visit_detail(request, pk):
    """
    View detailed information about a specific ANC visit.
    """
    visit = get_object_or_404(
        ANCVisit.objects.select_related('pregnancy__mother', 'recorded_by'),
        pk=pk,
        pregnancy__mother__facility=request.user.facility
    )
    
    context = {
        'page_title': f'ANC Visit {visit.visit_number} Details',
        'visit': visit,
    }
    return render(request, 'anc/visit_detail.html', context)


@login_required
def anc_visit_record(request, visit_id):
    """
    Record/complete an ANC visit.
    This is where nurses enter visit data.
    """
    visit = get_object_or_404(
        ANCVisit.objects.select_related('pregnancy__mother'),
        pk=visit_id,
        pregnancy__mother__facility=request.user.facility
    )
    
    # Don't allow editing completed visits
    if visit.attended:
        messages.warning(request, 'This visit has already been completed.')
        return redirect('anc_visit_detail', pk=visit.pk)
    
    if request.method == 'POST':
        form = ANCVisitForm(request.POST, instance=visit)
        if form.is_valid():
            anc_visit = form.save(commit=False)
            anc_visit.attended = True
            anc_visit.actual_visit_date = timezone.now().date()
            anc_visit.recorded_by = request.user
            anc_visit.save()
            
            messages.success(request, f'ANC Visit {visit.visit_number} recorded successfully!')
            return redirect('anc_visit_detail', pk=visit.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ANCVisitForm(instance=visit)
    
    context = {
        'page_title': f'Record ANC Visit {visit.visit_number}',
        'visit': visit,
        'form': form,
        'mother': visit.pregnancy.mother,
        'pregnancy': visit.pregnancy,
    }
    return render(request, 'anc/visit_record.html', context)


@login_required
def anc_visit_create(request):
    """
    Create/schedule a new ANC visit for a mother.
    """
    mother_id = request.GET.get('mother')
    pregnancy_id = request.GET.get('pregnancy')
    
    pregnancy = None
    if pregnancy_id:
        pregnancy = get_object_or_404(
            Pregnancy.objects.select_related('mother'),
            pk=pregnancy_id,
            mother__facility=request.user.facility
        )
    elif mother_id:
        mother = get_object_or_404(Mother, pk=mother_id, facility=request.user.facility)
        pregnancy = mother.pregnancies.filter(status='ACTIVE').first()
        if not pregnancy:
            messages.error(request, 'No active pregnancy found for this mother.')
            return redirect('mother_detail', pk=mother_id)
    
    if request.method == 'POST':
        form = ANCVisitForm(request.POST)
        if form.is_valid():
            visit = form.save(commit=False)
            visit.pregnancy = pregnancy
            visit.facility = request.user.facility
            visit.recorded_by = request.user
            
            # Auto-calculate visit number
            last_visit = ANCVisit.objects.filter(pregnancy=pregnancy).order_by('-visit_number').first()
            visit.visit_number = (last_visit.visit_number + 1) if last_visit else 1
            
            visit.save()
            
            messages.success(request, f'ANC Visit {visit.visit_number} scheduled successfully!')
            return redirect('anc_visit_detail', pk=visit.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        # Pre-fill some fields
        form = ANCVisitForm()
        if pregnancy:
            form.fields['scheduled_date'].initial = timezone.now().date() + timedelta(days=28)
    
    context = {
        'page_title': 'Schedule New ANC Visit',
        'form': form,
        'pregnancy': pregnancy,
    }
    return render(request, 'anc/visit_create.html', context)


@login_required
def anc_visit_edit(request, pk):
    """
    Edit an existing ANC visit (only if not completed).
    """
    visit = get_object_or_404(
        ANCVisit.objects.select_related('pregnancy__mother'),
        pk=pk,
        pregnancy__mother__facility=request.user.facility
    )
    
    # Don't allow editing completed visits
    if visit.attended:
        messages.warning(request, 'Cannot edit a completed visit.')
        return redirect('anc_visit_detail', pk=visit.pk)
    
    if request.method == 'POST':
        form = ANCVisitForm(request.POST, instance=visit)
        if form.is_valid():
            form.save()
            messages.success(request, 'Visit updated successfully!')
            return redirect('anc_visit_detail', pk=visit.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ANCVisitForm(instance=visit)
    
    context = {
        'page_title': f'Edit ANC Visit {visit.visit_number}',
        'visit': visit,
        'form': form,
    }
    return render(request, 'anc/visit_edit.html', context)