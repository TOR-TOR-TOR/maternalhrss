# apps/mothers/forms.py
from django import forms
from .models import Mother, Pregnancy


class MotherForm(forms.ModelForm):
    """
    Form for creating and editing mother records.
    """
    class Meta:
        model = Mother
        fields = [
            'first_name',
            'last_name',
            'date_of_birth',
            'national_id',
            'phone_number',
            'alternate_phone',
            'county',
            'sub_county',
            'ward',
            'village',
            'next_of_kin_name',
            'next_of_kin_phone',
            'next_of_kin_relationship',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Last name'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'type': 'date'
            }),
            'national_id': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'National ID number (optional)'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': '+254712345678'
            }),
            'alternate_phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Alternative phone (optional)'
            }),
            'county': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'County'
            }),
            'sub_county': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Sub-county'
            }),
            'ward': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Ward'
            }),
            'village': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Village (optional)'
            }),
            'next_of_kin_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Next of kin name'
            }),
            'next_of_kin_phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Next of kin phone'
            }),
            'next_of_kin_relationship': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Relationship (e.g., Husband, Mother, Sister)'
            }),
        }


class PregnancyForm(forms.ModelForm):
    """
    Form for creating and editing pregnancy records.
    """
    class Meta:
        model = Pregnancy
        fields = [
            'lmp',
            'pregnancy_number',
            'parity',
            'risk_level',
            'risk_factors',
            'previous_csection',
            'previous_complications',
            'notes',
        ]
        widgets = {
            'lmp': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'type': 'date'
            }),
            'pregnancy_number': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Gravida (G)',
                'min': '1'
            }),
            'parity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Para (P)',
                'min': '0'
            }),
            'risk_level': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500'
            }),
            'risk_factors': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'rows': '3',
                'placeholder': 'List risk factors: High BP, diabetes, previous C-section, age >35, etc.'
            }),
            'previous_csection': forms.CheckboxInput(attrs={
                'class': 'w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500'
            }),
            'previous_complications': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'rows': '3',
                'placeholder': 'Details of any previous pregnancy/delivery complications'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'rows': '3',
                'placeholder': 'Additional clinical notes'
            }),
        }