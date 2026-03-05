# apps/delivery/forms.py
from django import forms
from .models import Delivery, Baby
from apps.users.forms import apply_tailwind


# ─────────────────────────────────────────────
# Field Groups — single source of truth
# ─────────────────────────────────────────────

DELIVERY_BASIC_FIELDS      = ['delivery_date', 'delivery_time',
                               'delivery_type', 'delivery_outcome',
                               'number_of_babies']

DELIVERY_MOTHER_FIELDS     = ['mother_condition', 'complications', 'blood_loss_ml']

DELIVERY_PLACENTA_FIELDS   = ['placenta_complete', 'placenta_weight_grams']

DELIVERY_NOTES_FIELDS      = ['notes']

ALL_DELIVERY_FIELDS        = (DELIVERY_BASIC_FIELDS + DELIVERY_MOTHER_FIELDS +
                               DELIVERY_PLACENTA_FIELDS + DELIVERY_NOTES_FIELDS)

BABY_IDENTITY_FIELDS       = ['first_name', 'middle_name', 'last_name',
                               'gender', 'birth_order']

BABY_MEASUREMENTS_FIELDS   = ['birth_weight_grams', 'birth_length_cm',
                               'head_circumference_cm', 'apgar_score_1min',
                               'apgar_score_5min']

BABY_CONDITION_FIELDS      = ['health_condition', 'complications',
                               'required_resuscitation',
                               'birth_notification_number']

ALL_BABY_FIELDS            = (BABY_IDENTITY_FIELDS + BABY_MEASUREMENTS_FIELDS +
                               BABY_CONDITION_FIELDS)


# ─────────────────────────────────────────────
# Forms
# ─────────────────────────────────────────────

class DeliveryForm(forms.ModelForm):
    """
    Record a delivery event for an active pregnancy.
    facility and attended_by are set in the view, not exposed to the user.
    pregnancy is passed via URL, not the form.
    """

    class Meta:
        model  = Delivery
        fields = ALL_DELIVERY_FIELDS
        widgets = {
            'delivery_date':          forms.DateInput(attrs={'type': 'date'}),
            'delivery_time':          forms.TimeInput(attrs={'type': 'time'}),
            'mother_condition':       forms.TextInput(attrs={'placeholder': 'e.g. Stable, Critical'}),
            'complications':          forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe any complications…'}),
            'blood_loss_ml':          forms.NumberInput(attrs={'placeholder': 'ml'}),
            'placenta_weight_grams':  forms.NumberInput(attrs={'placeholder': 'grams'}),
            'number_of_babies':       forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'notes':                  forms.Textarea(attrs={'rows': 3, 'placeholder': 'Additional clinical notes…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['delivery_date'].required = True
        self.fields['delivery_time'].required = True
        apply_tailwind(self)

    def save(self, commit=True, pregnancy=None, facility=None, attended_by=None):
        """
        Attach pregnancy, facility, and attended_by before saving.
        Delivery.save() will auto-update pregnancy status.
        """
        delivery = super().save(commit=False)
        if pregnancy:
            delivery.pregnancy   = pregnancy
        if facility:
            delivery.facility    = facility
        if attended_by:
            delivery.attended_by = attended_by
        if commit:
            delivery.save()
        return delivery


class BabyForm(forms.ModelForm):
    """
    Register a baby after a delivery has been recorded.
    delivery, mother, facility, and registered_by are set in the view.
    """

    class Meta:
        model  = Baby
        fields = ALL_BABY_FIELDS
        widgets = {
            'first_name':                forms.TextInput(attrs={'placeholder': 'Optional — can be added later'}),
            'middle_name':               forms.TextInput(attrs={'placeholder': 'Optional'}),
            'last_name':                 forms.TextInput(attrs={'placeholder': 'Usually same as mother'}),
            'birth_weight_grams':        forms.NumberInput(attrs={'placeholder': 'e.g. 3200'}),
            'birth_length_cm':           forms.NumberInput(attrs={'placeholder': 'cm', 'step': '0.01'}),
            'head_circumference_cm':     forms.NumberInput(attrs={'placeholder': 'cm', 'step': '0.01'}),
            'apgar_score_1min':          forms.NumberInput(attrs={'min': 0, 'max': 10}),
            'apgar_score_5min':          forms.NumberInput(attrs={'min': 0, 'max': 10}),
            'health_condition':          forms.TextInput(attrs={'placeholder': 'e.g. Healthy, Needs monitoring'}),
            'complications':             forms.Textarea(attrs={'rows': 3, 'placeholder': 'Any birth complications…'}),
            'birth_notification_number': forms.TextInput(attrs={'placeholder': 'If registered'}),
            'birth_order':               forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['birth_weight_grams'].required = True
        self.fields['gender'].required             = True
        apply_tailwind(self)

    def clean_apgar_score_1min(self):
        score = self.cleaned_data.get('apgar_score_1min')
        if score is not None and not (0 <= score <= 10):
            raise forms.ValidationError("APGAR score must be between 0 and 10.")
        return score

    def clean_apgar_score_5min(self):
        score = self.cleaned_data.get('apgar_score_5min')
        if score is not None and not (0 <= score <= 10):
            raise forms.ValidationError("APGAR score must be between 0 and 10.")
        return score

    def save(self, commit=True, delivery=None, mother=None,
             facility=None, registered_by=None):
        """
        Attach delivery, mother, facility, registered_by before saving.
        Baby.save() signal will auto-generate immunization schedule.
        """
        baby = super().save(commit=False)
        if delivery:
            baby.delivery      = delivery
        if mother:
            baby.mother        = mother
        if facility:
            baby.facility      = facility
        if registered_by:
            baby.registered_by = registered_by
        if commit:
            baby.save()
        return baby