# apps/users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import CustomUser, Facility


# ─────────────────────────────────────────────
# Shared Helpers
# ─────────────────────────────────────────────

def active_facilities_queryset():
    """Single source of truth for facility dropdown filtering."""
    return Facility.objects.filter(is_active=True).order_by('county', 'name')


TAILWIND_INPUT   = 'input input-bordered w-full'
TAILWIND_SELECT  = 'select select-bordered w-full'
TAILWIND_TEXTAREA = 'textarea textarea-bordered w-full'


def apply_tailwind(form):
    """Apply DaisyUI classes to all fields in a form."""
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
    Accessible to MANAGER (own facility) and MOH (all facilities).
    """

    class Meta:
        model = Facility
        exclude = ['created_at', 'updated_at']
        widgets = {
            'name':             forms.TextInput(attrs={'placeholder': 'e.g. Nairobi West Hospital'}),
            'mfl_code':         forms.TextInput(attrs={'placeholder': 'e.g. 13046'}),
            'county':           forms.TextInput(attrs={'placeholder': 'e.g. Nairobi'}),
            'sub_county':       forms.TextInput(attrs={'placeholder': 'e.g. Langata'}),
            'ward':             forms.TextInput(attrs={'placeholder': 'e.g. Karen'}),
            'village':          forms.TextInput(attrs={'placeholder': 'Optional'}),
            'phone_number':     forms.TextInput(attrs={'placeholder': '+254712345678'}),
            'alternate_phone':  forms.TextInput(attrs={'placeholder': 'Optional'}),
            'email':            forms.EmailInput(attrs={'placeholder': 'facility@example.com'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        apply_tailwind(self)


# ─────────────────────────────────────────────
# User Forms
# ─────────────────────────────────────────────

class CustomUserCreationForm(UserCreationForm):
    """
    Register a new user.
    MOH-only view. Facility field limited to active facilities.
    MOH role may leave facility blank.
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
        super().__init__(*args, **kwargs)
        self.fields['facility'].queryset = active_facilities_queryset()
        self.fields['facility'].required = False
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        apply_tailwind(self)

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        facility = cleaned_data.get('facility')

        if role in ('NURSE', 'MANAGER') and not facility:
            self.add_error('facility', 'Nurses and Managers must be assigned to a facility.')

        return cleaned_data


class CustomUserUpdateForm(UserChangeForm):
    """
    Update an existing user's profile (no password fields).
    Used for both self-profile edits and admin edits.
    """
    password = None  # hide the raw password hash field UserChangeForm exposes

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
        self.fields['last_name'].required = True
        apply_tailwind(self)

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        facility = cleaned_data.get('facility')

        if role in ('NURSE', 'MANAGER') and not facility:
            self.add_error('facility', 'Nurses and Managers must be assigned to a facility.')

        return cleaned_data


class LoginForm(forms.Form):
    """
    Thin wrapper around Django's authenticate().
    Keeps auth logic in the view; form only handles input + styling.
    """
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