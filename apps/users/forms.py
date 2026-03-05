# apps/users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser, Facility


# ─────────────────────────────────────────────
# Shared Helpers
# ─────────────────────────────────────────────

def active_facilities_queryset():
    return Facility.objects.filter(is_active=True).order_by('county', 'name')


TAILWIND_INPUT    = 'input input-bordered w-full'
TAILWIND_SELECT   = 'select select-bordered w-full'
TAILWIND_TEXTAREA = 'textarea textarea-bordered w-full'


def apply_tailwind(form):
    for field in form.fields.values():
        widget = field.widget
        if isinstance(widget, (forms.Select, forms.RadioSelect)):
            widget.attrs.setdefault('class', TAILWIND_SELECT)
        elif isinstance(widget, forms.Textarea):
            widget.attrs.setdefault('class', TAILWIND_TEXTAREA)
        else:
            widget.attrs.setdefault('class', TAILWIND_INPUT)


# ─────────────────────────────────────────────
# Facility Forms
# ─────────────────────────────────────────────

class FacilityForm(forms.ModelForm):
    """
    Create / update a Facility.
    MOH: full access.
    MANAGER: cannot change facility_level or is_active.
    Pass is_manager=True to restrict fields.
    """

    class Meta:
        model = Facility
        exclude = ['created_at', 'updated_at']
        widgets = {
            'name':            forms.TextInput(attrs={'placeholder': 'e.g. Nairobi West Hospital'}),
            'mfl_code':        forms.TextInput(attrs={'placeholder': 'e.g. 13046'}),
            'county':          forms.TextInput(attrs={'placeholder': 'e.g. Nairobi'}),
            'sub_county':      forms.TextInput(attrs={'placeholder': 'e.g. Langata'}),
            'ward':            forms.TextInput(attrs={'placeholder': 'e.g. Karen'}),
            'village':         forms.TextInput(attrs={'placeholder': 'Optional'}),
            'phone_number':    forms.TextInput(attrs={'placeholder': '+254712345678'}),
            'alternate_phone': forms.TextInput(attrs={'placeholder': 'Optional'}),
            'email':           forms.EmailInput(attrs={'placeholder': 'facility@example.com'}),
        }

    def __init__(self, *args, **kwargs):
        self.is_manager = kwargs.pop('is_manager', False)
        super().__init__(*args, **kwargs)
        if self.is_manager:
            self.fields.pop('facility_level', None)
            self.fields.pop('is_active', None)
        apply_tailwind(self)


# ─────────────────────────────────────────────
# User Forms
# ─────────────────────────────────────────────

class CustomUserCreationForm(UserCreationForm):
    """
    Register a new user.
    MOH: full access — any role, any facility.
    MANAGER: restricted to NURSE role only, facility auto-assigned in view.
    Pass is_manager=True to restrict choices.
    """

    class Meta(UserCreationForm.Meta):
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
            'password2',
        ]

    def __init__(self, *args, **kwargs):
        self.is_manager = kwargs.pop('is_manager', False)
        super().__init__(*args, **kwargs)
        self.fields['facility'].queryset = active_facilities_queryset()
        self.fields['facility'].required = False
        self.fields['first_name'].required = True
        self.fields['last_name'].required  = True
        if self.is_manager:
            # Lock to Nurse only and hide facility (auto-assigned in view)
            self.fields['role'].choices = [('NURSE', 'Nurse / CHV')]
            self.fields['role'].initial  = 'NURSE'
            self.fields.pop('facility', None)
        apply_tailwind(self)

    def clean(self):
        cleaned_data = super().clean()
        role     = cleaned_data.get('role')
        facility = cleaned_data.get('facility')
        if not self.is_manager and role in ('NURSE', 'MANAGER') and not facility:
            self.add_error('facility', 'Nurses and Managers must be assigned to a facility.')
        return cleaned_data


class CustomUserUpdateForm(UserChangeForm):
    """
    MOH-only update form — full access to all fields.
    """
    password = None

    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'role',
            'facility',
            'is_active_user',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['facility'].queryset = active_facilities_queryset()
        self.fields['facility'].required = False
        self.fields['first_name'].required = True
        self.fields['last_name'].required  = True
        apply_tailwind(self)

    def clean(self):
        cleaned_data = super().clean()
        role     = cleaned_data.get('role')
        facility = cleaned_data.get('facility')
        if role in ('NURSE', 'MANAGER') and not facility:
            self.add_error('facility', 'Nurses and Managers must be assigned to a facility.')
        return cleaned_data


class ManagerUserUpdateForm(forms.ModelForm):
    """
    MANAGER editing a staff member.
    Can update personal details and active status only.
    Role and facility are MOH-only — not included.
    """

    class Meta:
        model = CustomUser
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'is_active_user',
        ]
        widgets = {
            'first_name':   forms.TextInput(attrs={'placeholder': 'First name'}),
            'last_name':    forms.TextInput(attrs={'placeholder': 'Last name'}),
            'email':        forms.EmailInput(attrs={'placeholder': 'email@example.com'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '+254712345678'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required  = True
        apply_tailwind(self)


class NurseProfileForm(forms.ModelForm):
    """
    Self-edit form for NURSE role.
    """

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name':   forms.TextInput(attrs={'placeholder': 'First name'}),
            'last_name':    forms.TextInput(attrs={'placeholder': 'Last name'}),
            'email':        forms.EmailInput(attrs={'placeholder': 'email@example.com'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '+254712345678'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required  = True
        apply_tailwind(self)


class ManagerProfileForm(forms.ModelForm):
    """
    Self-edit form for MANAGER role.
    """

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name':   forms.TextInput(attrs={'placeholder': 'First name'}),
            'last_name':    forms.TextInput(attrs={'placeholder': 'Last name'}),
            'email':        forms.EmailInput(attrs={'placeholder': 'email@example.com'}),
            'phone_number': forms.TextInput(attrs={'placeholder': '+254712345678'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required  = True
        apply_tailwind(self)


class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Username', 'autofocus': True})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind(self)