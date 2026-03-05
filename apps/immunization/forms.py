# apps/immunization/forms.py
from django import forms
from .models import ImmunizationSchedule
from apps.users.forms import apply_tailwind


# ─────────────────────────────────────────────
# Field Groups — single source of truth
# ─────────────────────────────────────────────

ADMINISTRATION_FIELDS  = ['administration_date', 'batch_number', 'expiry_date']
ADVERSE_FIELDS         = ['adverse_event', 'adverse_event_details']
NOTES_FIELDS           = ['notes']

ALL_RECORD_FIELDS      = ADMINISTRATION_FIELDS + ADVERSE_FIELDS + NOTES_FIELDS


# ─────────────────────────────────────────────
# Form
# ─────────────────────────────────────────────

class ImmunizationRecordForm(forms.ModelForm):
    """
    Record administration of a scheduled vaccine.
    The ImmunizationSchedule already exists (auto-generated when baby is registered).
    This form captures when it was given, batch info, and any adverse events.

    NOT used to create schedules — those are auto-generated via signal in delivery app.
    administered_by and facility are set in the view, not exposed here.
    """

    class Meta:
        model  = ImmunizationSchedule
        fields = ALL_RECORD_FIELDS
        widgets = {
            'administration_date':   forms.DateInput(attrs={'type': 'date'}),
            'expiry_date':           forms.DateInput(attrs={'type': 'date'}),
            'batch_number':          forms.TextInput(attrs={'placeholder': 'e.g. BN2024-001'}),
            'adverse_event_details': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe adverse event (fever, rash, swelling, etc.)…'
            }),
            'notes': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Additional notes…'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['administration_date'].required = True
        apply_tailwind(self)

    def clean(self):
        cleaned_data    = super().clean()
        adverse_event   = cleaned_data.get('adverse_event')
        adverse_details = cleaned_data.get('adverse_event_details', '').strip()

        if adverse_event and not adverse_details:
            self.add_error(
                'adverse_event_details',
                'Please describe the adverse event observed.'
            )
        return cleaned_data

    def clean_expiry_date(self):
        """Warn if vaccine expiry date is in the past."""
        from datetime import date
        expiry = self.cleaned_data.get('expiry_date')
        if expiry and expiry < date.today():
            raise forms.ValidationError(
                "This vaccine batch has expired. Do not administer an expired vaccine."
            )
        return expiry

    def save(self, commit=True, administered_by=None, facility=None):
        """
        Mark vaccine as administered and attach staff/facility before saving.
        Pass administered_by=request.user and facility=request.user.facility from view.
        """
        schedule = super().save(commit=False)
        schedule.administered = True
        schedule.missed       = False
        if administered_by:
            schedule.administered_by = administered_by
        if facility:
            schedule.facility = facility
        if commit:
            schedule.save()
        return schedule