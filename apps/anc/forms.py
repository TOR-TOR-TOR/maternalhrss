# apps/anc/forms.py
from django import forms
from .models import ANCVisit


class ANCVisitForm(forms.ModelForm):
    """
    Form for recording ANC visit data.
    """
    class Meta:
        model = ANCVisit
        fields = [
            'scheduled_date',
            'weight_kg',
            'blood_pressure',
            'hemoglobin',
            'fundal_height',
            'fetal_heartbeat',
            'iron_given',
            'folic_acid_given',
            'deworming_done',
            'tetanus_vaccine_given',
            'has_danger_signs',
            'danger_signs_notes',
            'clinical_notes',
            'next_visit_date',
        ]
        widgets = {
            'scheduled_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'type': 'date'
            }),
            'weight_kg': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Weight in kg',
                'step': '0.1',
                'min': '30',
                'max': '200'
            }),
            'blood_pressure': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'e.g., 120/80'
            }),
            'hemoglobin': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Hemoglobin level (g/dL)',
                'step': '0.1',
                'min': '5',
                'max': '20'
            }),
            'fundal_height': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Fundal height (cm)',
                'min': '10',
                'max': '50'
            }),
            'fetal_heartbeat': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'iron_given': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'folic_acid_given': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'deworming_done': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'tetanus_vaccine_given': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'has_danger_signs': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-red-600 border-gray-300 rounded focus:ring-red-500'
            }),
            'danger_signs_notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'rows': '3',
                'placeholder': 'Describe any danger signs observed...'
            }),
            'clinical_notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'rows': '4',
                'placeholder': 'Additional clinical notes, observations, or recommendations...'
            }),
            'next_visit_date': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'type': 'date'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        has_danger_signs = cleaned_data.get('has_danger_signs')
        danger_signs_notes = cleaned_data.get('danger_signs_notes')
        
        # If danger signs are checked, notes are required
        if has_danger_signs and not danger_signs_notes:
            self.add_error('danger_signs_notes', 'Please describe the danger signs observed.')
        
        return cleaned_data