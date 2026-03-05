# apps/anc/forms.py
from django import forms
from .models import ANCVisit
from apps.users.forms import apply_tailwind


# ─────────────────────────────────────────────
# Field Groups — single source of truth for
# which fields belong to each form section.
# Used by both the form and the template.
# ─────────────────────────────────────────────

CLINICAL_FIELDS    = ['actual_visit_date', 'weight_kg', 'blood_pressure',
                      'hemoglobin', 'fundal_height', 'fetal_heartbeat']

DANGER_FIELDS      = ['has_danger_signs', 'danger_signs_notes']

SUPPLEMENT_FIELDS  = ['iron_given', 'folic_acid_given',
                      'deworming_done', 'tetanus_vaccine_given']

NOTES_FIELDS       = ['clinical_notes', 'next_visit_date']

ALL_RECORD_FIELDS  = CLINICAL_FIELDS + DANGER_FIELDS + SUPPLEMENT_FIELDS + NOTES_FIELDS


class ANCVisitRecordForm(forms.ModelForm):
    """
    Used by nurses to record an attended ANC visit.
    The visit itself already exists (auto-generated at pregnancy registration).
    This form captures clinical measurements, danger signs, supplements, and notes.

    NOT used to create visits — those are auto-generated via signal.
    """

    class Meta:
        model  = ANCVisit
        fields = ALL_RECORD_FIELDS
        widgets = {
            'actual_visit_date':   forms.DateInput(attrs={'type': 'date'}),
            'next_visit_date':     forms.DateInput(attrs={'type': 'date'}),
            'weight_kg':           forms.NumberInput(attrs={'placeholder': 'e.g. 65.5', 'step': '0.01'}),
            'blood_pressure':      forms.TextInput(attrs={'placeholder': 'e.g. 120/80'}),
            'hemoglobin':          forms.NumberInput(attrs={'placeholder': 'e.g. 11.5', 'step': '0.1'}),
            'fundal_height':       forms.NumberInput(attrs={'placeholder': 'cm'}),
            'danger_signs_notes':  forms.Textarea(attrs={'rows': 3, 'placeholder': 'Describe danger signs observed…'}),
            'clinical_notes':      forms.Textarea(attrs={'rows': 4, 'placeholder': 'Clinical observations and notes…'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # actual_visit_date is required when recording a visit
        self.fields['actual_visit_date'].required = True
        apply_tailwind(self)

    def clean(self):
        cleaned_data = super().clean()
        has_danger   = cleaned_data.get('has_danger_signs')
        danger_notes = cleaned_data.get('danger_signs_notes', '').strip()

        if has_danger and not danger_notes:
            self.add_error(
                'danger_signs_notes',
                'Please describe the danger signs observed.'
            )
        return cleaned_data

    def save(self, commit=True, recorded_by=None):
        """
        Mark visit as attended and set recorded_by before saving.
        Pass recorded_by=request.user from the view.
        """
        visit = super().save(commit=False)
        visit.attended    = True
        visit.missed      = False
        if recorded_by:
            visit.recorded_by = recorded_by
        if commit:
            visit.save()
        return visit