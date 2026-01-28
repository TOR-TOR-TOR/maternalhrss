# apps/users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import CustomUser


class LoginForm(forms.Form):
    """
    Simple login form with username and password
    """
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'autofocus': True
        }),
        label='Username'
    )
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        }),
        label='Password'
    )


class PasswordChangeForm(forms.Form):
    """
    Form for users to change their own password
    Requires old password for security
    """
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        }),
        label='Current Password'
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        }),
        label='New Password',
        help_text='Password must be at least 8 characters long'
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        }),
        label='Confirm New Password'
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_old_password(self):
        """Verify that the old password is correct"""
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError('Your current password is incorrect.')
        return old_password
    
    def clean_new_password2(self):
        """Verify that the two password entries match"""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError('The two password fields didn\'t match.')
            
            # Validate password strength
            validate_password(password2, self.user)
        
        return password2
    
    def save(self, commit=True):
        """Save the new password"""
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


class PasswordResetForm(forms.Form):
    """
    Form for Managers/MOH to reset passwords for other users
    Only shows users from the same facility (for Managers)
    Shows all users (for MOH)
    """
    user = forms.ModelChoiceField(
        queryset=CustomUser.objects.none(),  # Will be set in __init__
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Select User',
        help_text='Choose the user whose password you want to reset'
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        }),
        label='New Password',
        help_text='Password must be at least 8 characters long'
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        }),
        label='Confirm New Password'
    )
    
    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # Set queryset based on current user's role
        if current_user:
            if current_user.role == 'MOH':
                # MOH can reset password for any user
                self.fields['user'].queryset = CustomUser.objects.filter(
                    is_active=True
                ).exclude(id=current_user.id).order_by('first_name', 'last_name')
            
            elif current_user.role == 'MANAGER':
                # Manager can only reset passwords for users in their facility
                self.fields['user'].queryset = CustomUser.objects.filter(
                    facility=current_user.facility,
                    is_active=True
                ).exclude(id=current_user.id).order_by('first_name', 'last_name')
    
    def clean_new_password2(self):
        """Verify that the two password entries match"""
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        
        if password1 and password2:
            if password1 != password2:
                raise ValidationError('The two password fields didn\'t match.')
            
            # Validate password strength
            user = self.cleaned_data.get('user')
            if user:
                validate_password(password2, user)
        
        return password2
    
    def save(self, commit=True):
        """Reset the user's password"""
        user = self.cleaned_data['user']
        password = self.cleaned_data['new_password1']
        user.set_password(password)
        if commit:
            user.save()
        return user


class UserRegistrationForm(UserCreationForm):
    """
    Form for registering new users
    Used by Managers/MOH to create new staff accounts
    """
    first_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    
    last_name = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'email@example.com'
        })
    )
    
    phone_number = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+254712345678'
        }),
        help_text='Format: +254712345678'
    )
    
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'role',
            'facility',
            'password1',
            'password2'
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
            'role': forms.Select(attrs={
                'class': 'form-control'
            }),
            'facility': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Customize password field widgets
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })