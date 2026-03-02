# apps/users/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views import View

from .forms import (
    FacilityForm,
    CustomUserCreationForm,
    CustomUserUpdateForm,
    LoginForm,
)
from .models import CustomUser, Facility


# ─────────────────────────────────────────────
# Access Control — single source of truth
# ─────────────────────────────────────────────

ROLE_REDIRECTS = {
    'NURSE':   'users:facility_list',
    'MANAGER': 'users:facility_list',
    'MOH':     'users:user_list',
}


def role_required(*roles):
    """
    Decorator for function-based views.
    Usage: @role_required('MOH') or @role_required('MOH', 'MANAGER')
    """
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
    """
    Mixin for class-based views.
    Set allowed_roles = ['MOH'] on the view class.
    """
    allowed_roles = []

    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        if request.user.role not in self.allowed_roles:
            messages.error(request, "You do not have permission to access that page.")
            return redirect(_role_home(request.user))
        return super().dispatch(request, *args, **kwargs)


def _role_home(user):
    """Return the named URL for a user's home based on their role."""
    return ROLE_REDIRECTS.get(user.role, 'users:login')


# ─────────────────────────────────────────────
# Shared Helpers
# ─────────────────────────────────────────────

def _handle_form(request, form, template, context=None):
    """
    DRY POST/GET handler for any ModelForm or Form.
    Returns (redirect_response | None, form).
    Caller decides where to redirect on success.
    """
    if request.method == 'POST':
        if form.is_valid():
            return True, form  # caller calls form.save() and redirects
    context = context or {}
    context['form'] = form
    return False, form


def _get_scoped_users(user):
    """Return user queryset scoped to the requesting user's role."""
    if user.role == 'MOH':
        return CustomUser.objects.select_related('facility').all()
    return CustomUser.objects.select_related('facility').filter(facility=user.facility)


def _get_scoped_facilities(user):
    """Return facility queryset scoped to the requesting user's role."""
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


@login_required
def logout_view(request):
    logout(request)
    return redirect('users:login')


# ─────────────────────────────────────────────
# User Views
# ─────────────────────────────────────────────

@role_required('MOH')
def register_view(request):
    form = CustomUserCreationForm(request.POST or None)
    success, form = _handle_form(request, form, 'users/register.html')
    if success:
        form.save()
        messages.success(request, "User registered successfully.")
        return redirect('users:user_list')
    return render(request, 'users/register.html', {'form': form, 'form_title': 'Register New User'})


@login_required
def profile_view(request):
    form = CustomUserUpdateForm(request.POST or None, instance=request.user)
    success, form = _handle_form(request, form, 'users/profile.html')
    if success:
        form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect('users:profile')
    return render(request, 'users/profile.html', {'form': form, 'form_title': 'Edit Profile'})


@role_required('MOH', 'MANAGER')
def user_list_view(request):
    users = _get_scoped_users(request.user)
    return render(request, 'users/user_list.html', {'users': users})


@role_required('MOH', 'MANAGER')
def user_detail_view(request, pk):
    qs = _get_scoped_users(request.user)
    user = get_object_or_404(qs, pk=pk)
    return render(request, 'users/user_detail.html', {'target_user': user})


@role_required('MOH', 'MANAGER')
def user_update_view(request, pk):
    qs = _get_scoped_users(request.user)
    target = get_object_or_404(qs, pk=pk)
    form = CustomUserUpdateForm(request.POST or None, instance=target)
    success, form = _handle_form(request, form, 'users/user_form.html')
    if success:
        form.save()
        messages.success(request, f"{target.get_full_name()} updated successfully.")
        return redirect('users:user_detail', pk=target.pk)
    return render(request, 'users/user_form.html', {
        'form': form,
        'form_title': f'Edit {target.get_full_name()}',
        'target_user': target,
    })


# ─────────────────────────────────────────────
# Facility Views
# ─────────────────────────────────────────────

@login_required
def facility_list_view(request):
    facilities = _get_scoped_facilities(request.user)
    return render(request, 'users/facility_list.html', {'facilities': facilities})


@login_required
def facility_detail_view(request, pk):
    qs = _get_scoped_facilities(request.user)
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
    


@role_required('MOH', 'MANAGER')
def facility_update_view(request, pk):
    qs = _get_scoped_facilities(request.user)
    facility = get_object_or_404(qs, pk=pk)

    # MANAGER can only edit their own facility
    if request.user.role == 'MANAGER' and request.user.facility_id != facility.pk:
        messages.error(request, "You can only edit your own facility.")
        return redirect('users:facility_detail', pk=facility.pk)

    form = FacilityForm(request.POST or None, instance=facility)
    success, form = _handle_form(request, form, 'users/facility_form.html')
    if success:
        form.save()
        messages.success(request, f"{facility.name} updated successfully.")
        return redirect('users:facility_detail', pk=facility.pk)
    return render(request, 'users/facility_form.html', {
        'form': form,
        'form_title': f'Edit {facility.name}',
        'facility': facility,
    })