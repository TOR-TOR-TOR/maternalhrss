# apps/mothers/forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Mother, Pregnancy
from datetime import date, timedelta
import re


class MotherForm(forms.ModelForm):
    """
    Form for creating and editing mother records with validation.
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
                'placeholder': 'First name',
                'required': True
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Last name',
                'required': True
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'type': 'date',
                'required': True
            }),
            'national_id': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'National ID number (optional)'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': '+254712345678',
                'required': True
            }),
            'alternate_phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Alternative phone (optional)'
            }),
            'county': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'County',
                'required': True
            }),
            'sub_county': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Sub-county',
                'required': True
            }),
            'ward': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Ward',
                'required': True
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
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name:
            raise ValidationError('First name is required.')
        if len(first_name) < 2:
            raise ValidationError('First name must be at least 2 characters.')
        if not re.match(r'^[a-zA-Z\s]+$', first_name):
            raise ValidationError('First name should only contain letters.')
        return first_name.strip().title()
    
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if not last_name:
            raise ValidationError('Last name is required.')
        if len(last_name) < 2:
            raise ValidationError('Last name must be at least 2 characters.')
        if not re.match(r'^[a-zA-Z\s]+$', last_name):
            raise ValidationError('Last name should only contain letters.')
        return last_name.strip().title()
    
    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if not dob:
            raise ValidationError('Date of birth is required.')
        
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        
        if dob > today:
            raise ValidationError('Date of birth cannot be in the future.')
        if age < 10:
            raise ValidationError('Mother must be at least 10 years old.')
        if age > 60:
            raise ValidationError('Please verify the date of birth. Age seems unusually high.')
        
        return dob
    
    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')
        if not phone:
            raise ValidationError('Phone number is required.')
        
        # Remove spaces and dashes
        phone = phone.replace(' ', '').replace('-', '')
        
        # Check Kenya phone format
        if not re.match(r'^\+?254\d{9}$', phone):
            raise ValidationError('Invalid phone format. Use: +254712345678 or 254712345678')
        
        # Ensure it starts with +254
        if not phone.startswith('+'):
            phone = '+' + phone
        
        return phone
    
    def clean_alternate_phone(self):
        phone = self.cleaned_data.get('alternate_phone')
        if phone:
            phone = phone.replace(' ', '').replace('-', '')
            if not re.match(r'^\+?254\d{9}$', phone):
                raise ValidationError('Invalid phone format. Use: +254712345678')
            if not phone.startswith('+'):
                phone = '+' + phone
        return phone
    
    def clean_national_id(self):
        national_id = self.cleaned_data.get('national_id')
        if national_id:
            national_id = national_id.strip()
            if len(national_id) < 5:
                raise ValidationError('National ID seems too short.')
        return national_id


class PregnancyForm(forms.ModelForm):
    """
    Form for creating and editing pregnancy records with validation.
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
                'type': 'date',
                'required': True
            }),
            'pregnancy_number': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Gravida (G)',
                'min': '1',
                'required': True
            }),
            'parity': forms.NumberInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'placeholder': 'Para (P)',
                'min': '0',
                'required': True
            }),
            'risk_level': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500',
                'required': True
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
    
    def clean_lmp(self):
        lmp = self.cleaned_data.get('lmp')
        if not lmp:
            raise ValidationError('Last Menstrual Period (LMP) is required.')
        
        today = date.today()
        
        if lmp > today:
            raise ValidationError('LMP cannot be in the future.')
        
        # Check if LMP is within reasonable range (not more than 10 months ago)
        days_ago = (today - lmp).days
        if days_ago > 320:  # ~10.5 months
            raise ValidationError('LMP is too far in the past. Please verify the date.')
        
        if days_ago < 0:
            raise ValidationError('LMP date is invalid.')
        
        return lmp
    
    def clean_pregnancy_number(self):
        pregnancy_number = self.cleaned_data.get('pregnancy_number')
        if not pregnancy_number:
            raise ValidationError('Pregnancy number (Gravida) is required.')
        if pregnancy_number < 1:
            raise ValidationError('Pregnancy number must be at least 1.')
        if pregnancy_number > 20:
            raise ValidationError('Pregnancy number seems unusually high. Please verify.')
        return pregnancy_number
    
    def clean_parity(self):
        parity = self.cleaned_data.get('parity')
        if parity is None:
            raise ValidationError('Parity is required.')
        if parity < 0:
            raise ValidationError('Parity cannot be negative.')
        if parity > 15:
            raise ValidationError('Parity seems unusually high. Please verify.')
        return parity
    
    def clean(self):
        cleaned_data = super().clean()
        pregnancy_number = cleaned_data.get('pregnancy_number')
        parity = cleaned_data.get('parity')
        
        # Parity cannot be greater than or equal to pregnancy number
        if pregnancy_number and parity is not None:
            if parity >= pregnancy_number:
                raise ValidationError({
                    'parity': 'Parity (P) must be less than Pregnancy number (G). '
                              'Parity is the number of previous births, while Gravida includes current pregnancy.'
                })
        
        return cleaned_data