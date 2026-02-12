# apps/users/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count
from django.utils import timezone
from datetime import timedelta
from apps.mothers.models import Mother, Pregnancy
from apps.anc.models import ANCVisit
from apps.reminders.models import SentReminder
from django.contrib.auth import (
    login, logout, authenticate,
    update_session_auth_hash,
    get_user_model
)
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.urls import reverse_lazy
from .forms import (
    LoginForm,
    PasswordResetForm,
    UserRegistrationForm,  # assuming you have this form
)
from .models import CustomUser

User = get_user_model()


def user_login(request):
    """
    Login view for all users (Nurses, Managers, MOH Admins).
    Redirects to role-specific dashboard after successful login.
    """
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                if user.is_active_user and user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.get_full_name()}!')
                    # Role-based redirect
                    if user.role == 'NURSE':
                        return redirect('nurse_dashboard')
                    elif user.role == 'MANAGER':
                        return redirect('manager_dashboard')
                    elif user.role == 'MOH':
                        return redirect('moh_dashboard')
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Your account has been deactivated. Contact administrator.')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    context = {
        'form': form,
        'page_title': 'Sign In - Maternal Health System'
    }
    return render(request, 'users/login.html', context)


@login_required
def user_logout(request):
    """Logout the current user and redirect to login page."""
    full_name = request.user.get_full_name()
    logout(request)
    messages.success(request, f'Goodbye, {full_name}! You have been logged out.')
    return redirect('login')


@login_required
def change_password(request):
    """Allow logged-in user to change their own password."""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Prevent logout after change
            messages.success(request, 'Your password has been updated successfully!')
            return redirect('password_change_done')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)

    context = {
        'form': form,
        'page_title': 'Change Your Password'
    }
    return render(request, 'users/change_password.html', context)


@login_required
def password_change_done(request):
    """Success page after user changes their own password."""
    context = {
        'page_title': 'Password Changed Successfully'
    }
    return render(request, 'users/password_change_done.html', context)


@login_required
def password_reset_request(request):
    """Allow MANAGER or MOH to reset password for another user."""
    if request.user.role not in ['MANAGER', 'MOH']:
        messages.error(request, 'You do not have permission to reset passwords.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = PasswordResetForm(request.POST, current_user=request.user)
        if form.is_valid():
            user = form.save()
            messages.success(
                request,
                f'Password reset successfully for {user.get_full_name()}. '
                f'Communicate the new password securely.'
            )
            return redirect('password_reset_done')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordResetForm(current_user=request.user)

    context = {
        'form': form,
        'page_title': 'Reset User Password'
    }
    return render(request, 'users/password_reset.html', context)


@login_required
def password_reset_done(request):
    """Success page after password reset by manager/MOH."""
    context = {
        'page_title': 'Password Reset Successfully'
    }
    return render(request, 'users/password_reset_done.html', context)


@login_required
def user_list(request):
    """
    List all users (filtered by role/facility).
    Only visible to MANAGER (own facility) and MOH (all).
    """
    if request.user.role not in ['MANAGER', 'MOH']:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    # Basic filtering
    users = User.objects.all().select_related('facility').order_by('role', 'last_name')

    if request.user.role == 'MANAGER':
        users = users.filter(facility=request.user.facility)

    context = {
        'users': users,
        'page_title': 'User Management'
    }
    return render(request, 'users/user_list.html', context)


@login_required
def user_create(request):
    """
    Create a new user account.
    Only allowed for MANAGER (creates in own facility) and MOH (any facility).
    """
    if request.user.role not in ['MANAGER', 'MOH']:
        messages.error(request, 'You do not have permission to create users.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            # If manager → force facility
            if request.user.role == 'MANAGER':
                user.facility = request.user.facility
            user.save()
            messages.success(request, f'User {user.get_full_name()} created successfully.')
            return redirect('user_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()

        # Pre-set facility for managers
        if request.user.role == 'MANAGER':
            form.fields['facility'].initial = request.user.facility
            form.fields['facility'].disabled = True

    context = {
        'form': form,
        'page_title': 'Create New User'
    }
    return render(request, 'users/user_create.html', context)


@login_required
def dashboard(request):
    """Central redirect to role-specific dashboard."""
    role_redirects = {
        'NURSE': 'nurse_dashboard',
        'MANAGER': 'manager_dashboard',
        'MOH': 'moh_dashboard',
    }
    redirect_to = role_redirects.get(request.user.role, 'dashboard')
    return redirect(redirect_to)


# Role-specific dashboard placeholders (to be expanded later)
@login_required
def nurse_dashboard(request):
    if request.user.role != 'NURSE':
        messages.error(request, 'Access denied. Nurses only.')
        return redirect('dashboard')

    context = {
        'page_title': 'Nurse Dashboard', 
        'user': request.user,
        'today_formatted': timezone.now().strftime('%A, %d %B %Y')
    }
    return render(request, 'dashboards/nurse_dashboard.html', context)


  
@login_required
def manager_dashboard(request):
    if request.user.role != 'MANAGER':
        messages.error(request, 'Access denied. Managers only.')
        return redirect('dashboard')
    context = {'page_title': 'Facility Manager Dashboard', 'user': request.user}
    return render(request, 'dashboards/manager_dashboard.html', context)


@login_required
def moh_dashboard(request):
    if request.user.role != 'MOH':
        messages.error(request, 'Access denied. MOH only.')
        return redirect('dashboard')
    context = {'page_title': 'MOH Dashboard', 'user': request.user}
    return render(request, 'dashboards/moh_dashboard.html', context)