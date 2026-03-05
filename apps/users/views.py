# apps/users/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View
from datetime import date, timedelta
from apps.anc.models import ANCVisit, get_upcoming_anc_visits, get_overdue_anc_visits
from apps.immunization.models import ImmunizationSchedule, get_upcoming_immunizations
from apps.mothers.models import Mother, Pregnancy
from apps.delivery.models import Delivery
from django.contrib.auth.views import PasswordChangeView, PasswordChangeDoneView
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse_lazy

from .forms import (
    FacilityForm,
    CustomUserCreationForm,
    CustomUserUpdateForm,
    ManagerUserUpdateForm,
    NurseProfileForm,
    ManagerProfileForm,
    LoginForm,
)
from .models import CustomUser, Facility


# ─────────────────────────────────────────────
# Access Control — single source of truth
# ─────────────────────────────────────────────

ROLE_REDIRECTS = {
    'NURSE':   'users:nurse_dashboard',
    'MANAGER': 'users:manager_dashboard',
    'MOH':     'users:user_list',
}


def role_required(*roles):
    def decorator(view_func):
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.role not in roles:
                messages.error(request, "You do not have permission to access that page.")
                return redirect(_role_home(request.user))
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


class RoleRequiredMixin:
    allowed_roles = []

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in self.allowed_roles:
            messages.error(request, "You do not have permission to access that page.")
            return redirect(_role_home(request.user))
        return super().dispatch(request, *args, **kwargs)


def _role_home(user):
    return ROLE_REDIRECTS.get(user.role, 'users:login')


# ─────────────────────────────────────────────
# Shared Helpers
# ─────────────────────────────────────────────

def _handle_form(request, form, template, context=None):
    if request.method == 'POST':
        if form.is_valid():
            return True, form
    context = context or {}
    context['form'] = form
    return False, form


def _get_scoped_users(user):
    if user.role == 'MOH':
        return CustomUser.objects.select_related('facility').all()
    return CustomUser.objects.select_related('facility').filter(facility=user.facility)


def _get_scoped_facilities(user):
    if user.role == 'MOH':
        return Facility.objects.all()
    return Facility.objects.filter(pk=user.facility_id)


# ─────────────────────────────────────────────
# Auth Views
# ─────────────────────────────────────────────

class LoginView(View):
    template_name = 'users/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect(_role_home(request.user))
        return render(request, self.template_name, {'form': LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
            )
            if user and user.is_active_user:
                login(request, user)
                return redirect(_role_home(user))
            messages.error(request, "Invalid credentials or account disabled.")
        return render(request, self.template_name, {'form': form})


class StyledPasswordChangeView(PasswordChangeView):
    template_name = 'registration/password_change_form.html'
    success_url   = reverse_lazy('users:password_change_done')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            field.widget.attrs['class'] = 'input input-bordered w-full'
        return form


class StyledPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'registration/password_change_done.html'


@login_required
def logout_view(request):
    logout(request)
    return redirect('users:login')


# ─────────────────────────────────────────────
# Nurse Dashboard
# ─────────────────────────────────────────────

@login_required
def nurse_dashboard_view(request):
    facility = request.user.facility
    if not facility:
        messages.warning(request, "You have not been assigned to a facility yet.")
        return redirect('users:profile')

    today = date.today()

    active_pregnancies = Pregnancy.objects.filter(
        facility=facility, status='ACTIVE'
    ).count()

    anc_today = ANCVisit.objects.filter(
        facility=facility, scheduled_date=today,
        attended=False, missed=False,
    ).count()

    vaccines_this_week = ImmunizationSchedule.objects.filter(
        facility=facility,
        scheduled_date__range=[today, today + timedelta(days=7)],
        administered=False, missed=False,
    ).count()

    danger_signs_30d = ANCVisit.objects.filter(
        facility=facility,
        has_danger_signs=True,
        attended=True,
        actual_visit_date__gte=today - timedelta(days=30),
    ).count()

    todays_anc = ANCVisit.objects.filter(
        facility=facility, scheduled_date=today,
        attended=False, missed=False,
    ).select_related('pregnancy__mother', 'pregnancy').order_by('visit_number')

    todays_vaccines = ImmunizationSchedule.objects.filter(
        facility=facility, scheduled_date=today,
        administered=False, missed=False,
    ).select_related('baby__mother', 'vaccine').order_by('scheduled_date')

    overdue_anc = ANCVisit.objects.filter(
        facility=facility, scheduled_date__lt=today,
        attended=False, missed=False, pregnancy__status='ACTIVE',
    ).select_related('pregnancy__mother', 'pregnancy').order_by('scheduled_date')[:10]

    high_risk_near_edd = Pregnancy.objects.filter(
        facility=facility, status='ACTIVE', risk_level='HIGH',
        edd__lte=today + timedelta(weeks=2), edd__gte=today,
    ).select_related('mother').order_by('edd')[:5]

    overdue_vaccines = ImmunizationSchedule.objects.filter(
        facility=facility, scheduled_date__lt=today,
        administered=False, missed=False,
    ).select_related('baby__mother', 'vaccine').order_by('scheduled_date')[:10]

    recent_mothers = Mother.objects.filter(
        facility=facility,
    ).select_related('facility').order_by('-registration_date')[:5]

    recent_anc = ANCVisit.objects.filter(
        facility=facility, recorded_by=request.user, attended=True,
    ).select_related('pregnancy__mother').order_by('-actual_visit_date')[:5]

    return render(request, 'users/nurse_dashboard.html', {
        'active_pregnancies':  active_pregnancies,
        'anc_today':           anc_today,
        'vaccines_this_week':  vaccines_this_week,
        'danger_signs_30d':    danger_signs_30d,   # ← fixed name
        'todays_anc':          todays_anc,
        'todays_vaccines':     todays_vaccines,
        'overdue_anc':         overdue_anc,
        'high_risk_near_edd':  high_risk_near_edd,
        'overdue_vaccines':    overdue_vaccines,
        'recent_mothers':      recent_mothers,
        'recent_anc':          recent_anc,         # ← fixed name
        'today':               today,
        'facility':            facility,
    })


# ─────────────────────────────────────────────
# Manager Dashboard
# ─────────────────────────────────────────────

@login_required
def manager_dashboard_view(request):
    if request.user.role != 'MANAGER':
        return redirect(_role_home(request.user))

    facility = request.user.facility
    if not facility:
        messages.warning(request, "You have not been assigned to a facility yet.")
        return redirect('users:profile')

    today = date.today()

    total_staff = CustomUser.objects.filter(
        facility=facility, is_active_user=True,
    ).exclude(role='MANAGER').count()

    active_pregnancies = Pregnancy.objects.filter(
        facility=facility, status='ACTIVE',
    ).count()

    high_risk_count = Pregnancy.objects.filter(
        facility=facility, status='ACTIVE', risk_level='HIGH',
    ).count()

    deliveries_this_month = Delivery.objects.filter(
        facility=facility,
        delivery_date__year=today.year,
        delivery_date__month=today.month,
    ).count()

    anc_this_week = ANCVisit.objects.filter(
        facility=facility,
        scheduled_date__range=[today, today + timedelta(days=7)],
        attended=False, missed=False,
    ).count()

    overdue_anc_count = ANCVisit.objects.filter(
        facility=facility, scheduled_date__lt=today,
        attended=False, missed=False, pregnancy__status='ACTIVE',
    ).count()

    danger_signs_30d = ANCVisit.objects.filter(
        facility=facility, has_danger_signs=True, attended=True,
        actual_visit_date__gte=today - timedelta(days=30),
    ).count()

    overdue_vaccines_count = ImmunizationSchedule.objects.filter(
        facility=facility, scheduled_date__lt=today,
        administered=False, missed=False,
    ).count()

    staff = CustomUser.objects.filter(
        facility=facility, is_active_user=True,
    ).exclude(role='MANAGER').order_by('role', 'first_name')

    high_risk_pregnancies = Pregnancy.objects.filter(
        facility=facility, status='ACTIVE', risk_level='HIGH',
    ).select_related('mother').order_by('edd')[:8]

    overdue_anc = ANCVisit.objects.filter(
        facility=facility, scheduled_date__lt=today,
        attended=False, missed=False, pregnancy__status='ACTIVE',
    ).select_related('pregnancy__mother', 'recorded_by').order_by('scheduled_date')[:8]

    recent_deliveries = Delivery.objects.filter(
        facility=facility,
    ).select_related('pregnancy__mother', 'attended_by').order_by('-delivery_date')[:5]

    recent_mothers = Mother.objects.filter(
        facility=facility,
    ).select_related('registered_by').order_by('-registration_date')[:5]

    return render(request, 'users/manager_dashboard.html', {
        'total_staff':            total_staff,
        'active_pregnancies':     active_pregnancies,
        'high_risk_count':        high_risk_count,
        'deliveries_this_month':  deliveries_this_month,
        'anc_this_week':          anc_this_week,
        'overdue_anc_count':      overdue_anc_count,
        'danger_signs_30d':       danger_signs_30d,
        'overdue_vaccines_count': overdue_vaccines_count,
        'staff':                  staff,
        'high_risk_pregnancies':  high_risk_pregnancies,
        'overdue_anc':            overdue_anc,
        'recent_deliveries':      recent_deliveries,
        'recent_mothers':         recent_mothers,
        'today':                  today,
        'facility':               facility,
    })


# ─────────────────────────────────────────────
# User Views
# ─────────────────────────────────────────────

@role_required('MOH', 'MANAGER')
def register_view(request):
    is_manager = request.user.role == 'MANAGER'
    form = CustomUserCreationForm(
        request.POST or None,
        is_manager=is_manager,
    )
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        if is_manager:
            user.role     = 'NURSE'
            user.facility = request.user.facility
        user.save()
        messages.success(request, f"{user.get_full_name()} registered successfully.")
        return redirect('users:user_list')

    return render(request, 'users/register.html', {
        'form':       form,
        'form_title': 'Add Staff' if is_manager else 'Register New User',
    })


@login_required
def profile_view(request):
    if request.user.role == 'NURSE':
        form = NurseProfileForm(request.POST or None, instance=request.user)
    elif request.user.role == 'MANAGER':
        form = ManagerProfileForm(request.POST or None, instance=request.user)
    else:
        form = CustomUserUpdateForm(request.POST or None, instance=request.user)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('users:profile')

    return render(request, 'users/profile.html', {
        'form':       form,
        'form_title': 'Edit Profile',
    })


@role_required('MOH', 'MANAGER')
def user_list_view(request):
    users = _get_scoped_users(request.user)
    return render(request, 'users/user_list.html', {'users': users})


@role_required('MOH', 'MANAGER')
def user_detail_view(request, pk):
    qs   = _get_scoped_users(request.user)
    user = get_object_or_404(qs, pk=pk)
    return render(request, 'users/user_detail.html', {'target_user': user})


@role_required('MOH', 'MANAGER')
def user_update_view(request, pk):
    qs     = _get_scoped_users(request.user)
    target = get_object_or_404(qs, pk=pk)

    if request.user.role == 'MANAGER':
        form = ManagerUserUpdateForm(request.POST or None, instance=target)
    else:
        form = CustomUserUpdateForm(request.POST or None, instance=target)

    success, form = _handle_form(request, form, 'users/user_form.html')
    if success:
        form.save()
        messages.success(request, f"{target.get_full_name()} updated successfully.")
        return redirect('users:user_detail', pk=target.pk)

    return render(request, 'users/user_form.html', {
        'form':        form,
        'form_title':  f'Edit {target.get_full_name()}',
        'target_user': target,
    })



# ─────────────────────────────────────────────
# Facility Views
# ─────────────────────────────────────────────

@login_required
def facility_list_view(request):
    facilities = _get_scoped_facilities(request.user)
    if request.user.role == 'NURSE':
        if request.user.facility_id:
            return redirect('users:facility_detail', pk=request.user.facility_id)
        messages.warning(request, "You have not been assigned to a facility yet.")
        return redirect('users:profile')
    return render(request, 'users/facility_list.html', {'facilities': facilities})


@login_required
def facility_detail_view(request, pk):
    qs       = _get_scoped_facilities(request.user)
    facility = get_object_or_404(qs, pk=pk)
    return render(request, 'users/facility_detail.html', {'facility': facility})


@role_required('MOH')
def facility_create_view(request):
    form = FacilityForm(request.POST or None)
    success, form = _handle_form(request, form, 'users/facility_form.html')
    if success:
        facility = form.save()
        messages.success(request, f"{facility.name} created successfully.")
        return redirect('users:facility_detail', pk=facility.pk)
    return render(request, 'users/facility_form.html', {
        'form':       form,
        'form_title': 'Add New Facility',
    })


@role_required('MOH', 'MANAGER')
def facility_update_view(request, pk):
    qs       = _get_scoped_facilities(request.user)
    facility = get_object_or_404(qs, pk=pk)

    if request.user.role == 'MANAGER' and request.user.facility_id != facility.pk:
        messages.error(request, "You can only edit your own facility.")
        return redirect('users:facility_detail', pk=facility.pk)

    is_manager = request.user.role == 'MANAGER'
    form = FacilityForm(
        request.POST or None,
        instance=facility,
        is_manager=is_manager,        # ← restricts facility_level + is_active
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, f"{facility.name} updated successfully.")
        return redirect('users:facility_detail', pk=facility.pk)

    return render(request, 'users/facility_form.html', {
        'form':       form,
        'form_title': f'Edit {facility.name}',
        'facility':   facility,
    })