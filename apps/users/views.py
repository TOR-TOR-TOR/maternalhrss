# apps/users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .forms import LoginForm, PasswordResetForm, PasswordChangeForm


def user_login(request):
    """
    Login view for all users (Nurses, Managers, MOH Admins)
    Redirects to appropriate dashboard based on role
    """
    # If user is already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            
            # Authenticate user
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # Check if user account is active
                if user.is_active_user and user.is_active:
                    login(request, user)
                    messages.success(request, f'Welcome back, {user.get_full_name()}!')
                    
                    # Redirect to appropriate dashboard based on role
                    if user.role == 'NURSE':
                        return redirect('nurse_dashboard')
                    elif user.role == 'MANAGER':
                        return redirect('manager_dashboard')
                    elif user.role == 'MOH':
                        return redirect('moh_dashboard')
                    else:
                        return redirect('dashboard')  # Default dashboard
                else:
                    messages.error(request, 'Your account has been deactivated. Please contact the administrator.')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    
    context = {
        'form': form,
        'page_title': 'Login - Maternal Health System'
    }
    return render(request, 'users/login.html', context)


@login_required
def user_logout(request):
    """
    Logout view - logs out user and redirects to login page
    """
    user_name = request.user.get_full_name()
    logout(request)
    messages.success(request, f'Goodbye, {user_name}! You have been logged out successfully.')
    return redirect('login')


@login_required
def change_password(request):
    """
    Allow logged-in users to change their password
    Requires old password for security
    """
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Important: Update session to prevent logout after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PasswordChangeForm(request.user)
    
    context = {
        'form': form,
        'page_title': 'Change Password'
    }
    return render(request, 'users/change_password.html', context)


@login_required
def password_reset_request(request):
    """
    Admin/Manager can reset passwords for other users
    Only accessible by MANAGER or MOH roles
    """
    # Check if user has permission to reset passwords
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
                f'New password has been set.'
            )
            return redirect('user_list')  # Redirect to user management page
    else:
        form = PasswordResetForm(current_user=request.user)
    
    context = {
        'form': form,
        'page_title': 'Reset User Password'
    }
    return render(request, 'users/password_reset.html', context)


@login_required
def dashboard(request):
    """
    Default dashboard - redirects to role-specific dashboard
    """
    if request.user.role == 'NURSE':
        return redirect('nurse_dashboard')
    elif request.user.role == 'MANAGER':
        return redirect('manager_dashboard')
    elif request.user.role == 'MOH':
        return redirect('moh_dashboard')
    else:
        # Fallback for users without specific role
        context = {
            'user': request.user,
            'page_title': 'Dashboard'
        }
        return render(request, 'users/dashboard.html', context)


# Placeholder views for role-specific dashboards
# These will be implemented later in apps/dashboards/

@login_required
def nurse_dashboard(request):
    """Placeholder for nurse dashboard"""
    if request.user.role != 'NURSE':
        messages.error(request, 'Access denied. Nurses only.')
        return redirect('dashboard')
    
    context = {
        'page_title': 'Nurse Dashboard',
        'user': request.user
    }
    return render(request, 'dashboards/nurse_dashboard.html', context)


@login_required
def manager_dashboard(request):
    """Placeholder for facility manager dashboard"""
    if request.user.role != 'MANAGER':
        messages.error(request, 'Access denied. Facility Managers only.')
        return redirect('dashboard')
    
    context = {
        'page_title': 'Facility Manager Dashboard',
        'user': request.user
    }
    return render(request, 'dashboards/manager_dashboard.html', context)


@login_required
def moh_dashboard(request):
    """Placeholder for MOH administrator dashboard"""
    if request.user.role != 'MOH':
        messages.error(request, 'Access denied. MOH Administrators only.')
        return redirect('dashboard')
    
    context = {
        'page_title': 'MOH Dashboard',
        'user': request.user
    }
    return render(request, 'dashboards/moh_dashboard.html', context)