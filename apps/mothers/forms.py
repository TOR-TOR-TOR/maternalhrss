# apps/mothers/forms.py
from django import forms
from .models import Mother, Pregnancy
from apps.users.forms import apply_tailwind


# ─────────────────────────────────────────────
# Field Groups — single source of truth
# ─────────────────────────────────────────────

MOTHER_PERSONAL_FIELDS    = ['first_name', 'last_name', 'date_of_birth', 'national_id']
MOTHER_CONTACT_FIELDS     = ['phone_number', 'alternate_phone']
MOTHER_LOCATION_FIELDS    = ['county', 'sub_county', 'ward', 'village']
MOTHER_NOK_FIELDS         = ['next_of_kin_name', 'next_of_kin_phone',
                              'next_of_kin_relationship']
MOTHER_STATUS_FIELDS      = ['is_active']

ALL_MOTHER_FIELDS         = (MOTHER_PERSONAL_FIELDS + MOTHER_CONTACT_FIELDS +
                              MOTHER_LOCATION_FIELDS + MOTHER_NOK_FIELDS)

ALL_MOTHER_UPDATE_FIELDS  = ALL_MOTHER_FIELDS + MOTHER_STATUS_FIELDS

PREGNANCY_BASIC_FIELDS    = ['lmp', 'pregnancy_number', 'parity']
PREGNANCY_RISK_FIELDS     = ['risk_level', 'risk_factors', 'previous_csection',
                              'previous_complications']
PREGNANCY_NOTES_FIELDS    = ['notes']

ALL_PREGNANCY_FIELDS      = (PREGNANCY_BASIC_FIELDS + PREGNANCY_RISK_FIELDS +
                              PREGNANCY_NOTES_FIELDS)


# ─────────────────────────────────────────────
# Mother Forms
# ─────────────────────────────────────────────

class MotherRegistrationForm(forms.ModelForm):
    """
    Register a new mother.
    facility and registered_by are set in the view, not exposed here.
    """

    class Meta:
        model  = Mother
        fields = ALL_MOTHER_FIELDS
        widgets = {
            'first_name':               forms.TextInput(attrs={'placeholder': 'First name'}),
            'last_name':                forms.TextInput(attrs={'placeholder': 'Last name'}),
            'date_of_birth':            forms.DateInput(attrs={'type': 'date'}),
            'national_id':              forms.TextInput(attrs={'placeholder': 'Optional'}),
            'phone_number':             forms.TextInput(attrs={'placeholder': '+254712345678'}),
            'alternate_phone':          forms.TextInput(attrs={'placeholder': 'Optional'}),
            'county':                   forms.TextInput(attrs={'placeholder': 'e.g. Nairobi'}),
            'sub_county':               forms.TextInput(attrs={'placeholder': 'e.g. Langata'}),
            'ward':                     forms.TextInput(attrs={'placeholder': 'e.g. Karen'}),
            'village':                  forms.TextInput(attrs={'placeholder': 'Optional'}),
            'next_of_kin_name':         forms.TextInput(attrs={'placeholder': 'Full name'}),
            'next_of_kin_phone':        forms.TextInput(attrs={'placeholder': '+254712345678'}),
            'next_of_kin_relationship': forms.TextInput(attrs={'placeholder': 'e.g. Husband, Sister'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required  = True
        self.fields['last_name'].required   = True
        self.fields['phone_number'].required = True
        self.fields['date_of_birth'].required = True
        self.fields['county'].required      = True
        self.fields['sub_county'].required  = True
        self.fields['ward'].required        = True
        apply_tailwind(self)

    def clean_date_of_birth(self):
        """Mother must be at least 10 years old (safeguard against data entry errors)."""
        from datetime import date
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            age = (date.today() - dob).days // 365
            if age < 10:
                raise forms.ValidationError("Please check the date of birth entered.")
            if dob > date.today():
                raise forms.ValidationError("Date of birth cannot be in the future.")
        return dob

    def save(self, commit=True, facility=None, registered_by=None):
        """Attach facility and registered_by before saving."""
        mother = super().save(commit=False)
        if facility:
            mother.facility      = facility
        if registered_by:
            mother.registered_by = registered_by
        if commit:
            mother.save()
        return mother


class MotherUpdateForm(MotherRegistrationForm):
    """
    Update an existing mother's record.
    Extends MotherRegistrationForm adding the is_active status field.
    All validation and save() logic inherited.
    """

    class Meta(MotherRegistrationForm.Meta):
        fields = ALL_MOTHER_UPDATE_FIELDS


# ─────────────────────────────────────────────
# Pregnancy Form
# ─────────────────────────────────────────────

class PregnancyForm(forms.ModelForm):
    """
    Register a new pregnancy for an existing mother.
    mother, facility, and registered_by are set in the view via URL/session.
    edd and gestational_age_weeks are auto-calculated in Pregnancy.save().
    """

    class Meta:
        model  = Pregnancy
        fields = ALL_PREGNANCY_FIELDS
        widgets = {
            'lmp':                    forms.DateInput(attrs={'type': 'date'}),
            'pregnancy_number':       forms.NumberInput(attrs={'min': 1, 'placeholder': 'e.g. 1'}),
            'parity':                 forms.NumberInput(attrs={'min': 0, 'placeholder': 'e.g. 0'}),
            'risk_factors':           forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'e.g. High BP, diabetes, age >35, previous C-section…'
            }),
            'previous_complications': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Details of any previous pregnancy complications…'
            }),
            'notes':                  forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Additional clinical notes…'
            }),
        }

    def __init__(self, *args, **kwargs):
        # Accept mother kwarg to auto-set pregnancy_number
        self.mother = kwargs.pop('mother', None)
        super().__init__(*args, **kwargs)
        self.fields['lmp'].required              = True
        self.fields['pregnancy_number'].required = True
        self.fields['parity'].required           = True

        # Pre-fill pregnancy_number as next in sequence
        if self.mother and not self.instance.pk:
            next_num = self.mother.total_pregnancies + 1
            self.fields['pregnancy_number'].initial = next_num

        apply_tailwind(self)

    def clean_lmp(self):
        """LMP cannot be in the future and must be within the last 10 months."""
        from datetime import date
        lmp = self.cleaned_data.get('lmp')
        if lmp:
            if lmp > date.today():
                raise forms.ValidationError("LMP cannot be in the future.")
            days_ago = (date.today() - lmp).days
            if days_ago > 300:  # ~10 months — beyond full term
                raise forms.ValidationError(
                    "LMP is more than 10 months ago. Please verify the date."
                )
        return lmp

    def clean(self):
        cleaned_data      = super().clean()
        risk_level        = cleaned_data.get('risk_level')
        risk_factors      = cleaned_data.get('risk_factors', '').strip()
        prev_csection     = cleaned_data.get('previous_csection')
        prev_comp         = cleaned_data.get('previous_complications', '').strip()

        # If marked high/medium risk, require risk factors description
        if risk_level in ('HIGH', 'MEDIUM') and not risk_factors:
            self.add_error(
                'risk_factors',
                'Please describe the risk factors for this risk level.'
            )

        # If previous C-section, encourage documenting complications
        if prev_csection and not prev_comp:
            self.add_error(
                'previous_complications',
                'Please document details of the previous C-section.'
            )

        return cleaned_data

    def save(self, commit=True, mother=None, facility=None, registered_by=None):
        """
        Attach mother, facility, registered_by before saving.
        Pregnancy.save() auto-calculates EDD and gestational age.
        Signal in anc app auto-generates 8 ANC contacts after save.
        """
        pregnancy = super().save(commit=False)
        if mother:
            pregnancy.mother        = mother
        if facility:
            pregnancy.facility      = facility
        if registered_by:
            pregnancy.registered_by = registered_by
        if commit:
            pregnancy.save()
        return pregnancy