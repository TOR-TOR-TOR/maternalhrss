# apps/mothers/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Mother, Pregnancy
from .forms import MotherForm, PregnancyForm  # You'll need to create these forms
from django.utils import timezone


@login_required
def mother_list(request):
    """
    List all mothers in the nurse's facility with search and filtering.
    """
    facility = request.user.facility
    
    # Base queryset
    mothers = Mother.objects.filter(facility=facility).select_related('facility').order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        mothers = mothers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(mother_id__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(national_id__icontains=search_query)
        )
    
    # Filter by pregnancy status
    status_filter = request.GET.get('status', '')
    if status_filter:
        mothers = mothers.filter(pregnancies__status=status_filter).distinct()
    
    # Filter by risk level
    risk_filter = request.GET.get('risk', '')
    if risk_filter:
        mothers = mothers.filter(pregnancies__risk_level=risk_filter).distinct()
    
    # Pagination
    paginator = Paginator(mothers, 20)  # 20 mothers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_title': 'Mother Records',
        'mothers': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'risk_filter': risk_filter,
        'total_count': mothers.count(),
    }
    return render(request, 'mothers/mother_list.html', context)


@login_required
def mother_detail(request, pk):
    """
    View detailed information about a specific mother.
    """
    mother = get_object_or_404(Mother, pk=pk, facility=request.user.facility)
    
    # Get all pregnancies for this mother
    pregnancies = mother.pregnancies.all().order_by('-lmp')
    
    # Get active pregnancy if exists
    active_pregnancy = pregnancies.filter(status='ACTIVE').first()
    
    context = {
        'page_title': f'{mother.get_full_name()} - Details',
        'mother': mother,
        'pregnancies': pregnancies,
        'active_pregnancy': active_pregnancy,
    }
    return render(request, 'mothers/mother_detail.html', context)


@login_required
def mother_create(request):
    """
    Register a new mother.
    """
    if request.method == 'POST':
        mother_form = MotherForm(request.POST)
        pregnancy_form = PregnancyForm(request.POST)
        
        if mother_form.is_valid() and pregnancy_form.is_valid():
            # Save mother
            mother = mother_form.save(commit=False)
            mother.facility = request.user.facility
            mother.save()
            
            # Save pregnancy
            pregnancy = pregnancy_form.save(commit=False)
            pregnancy.mother = mother
            pregnancy.save()
            
            messages.success(request, f'Mother {mother.get_full_name()} registered successfully!')
            return redirect('mother_detail', pk=mother.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        mother_form = MotherForm()
        pregnancy_form = PregnancyForm()
    
    context = {
        'page_title': 'Register New Mother',
        'mother_form': mother_form,
        'pregnancy_form': pregnancy_form,
    }
    return render(request, 'mothers/mother_create.html', context)


@login_required
def mother_edit(request, pk):
    """
    Edit mother information.
    """
    mother = get_object_or_404(Mother, pk=pk, facility=request.user.facility)
    
    if request.method == 'POST':
        form = MotherForm(request.POST, instance=mother)
        if form.is_valid():
            form.save()
            messages.success(request, f'Mother {mother.get_full_name()} updated successfully!')
            return redirect('mother_detail', pk=mother.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = MotherForm(instance=mother)
    
    context = {
        'page_title': f'Edit {mother.get_full_name()}',
        'mother': mother,
        'form': form,
    }
    return render(request, 'mothers/mother_edit.html', context)


@login_required
def mother_delete(request, pk):
    """
    Delete a mother record (soft delete recommended).
    """
    mother = get_object_or_404(Mother, pk=pk, facility=request.user.facility)
    
    if request.method == 'POST':
        mother_name = mother.get_full_name()
        mother.delete()
        messages.success(request, f'Mother {mother_name} has been deleted.')
        return redirect('mother_list')
    
    context = {
        'page_title': f'Delete {mother.get_full_name()}',
        'mother': mother,
    }
    return render(request, 'mothers/mother_delete.html', context)