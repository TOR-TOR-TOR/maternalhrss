# apps/mothers/forms.py
from django import forms
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from .models import Mother, Pregnancy


class MotherRegistrationForm(forms.ModelForm):
    """
    Form for registering new mothers in the system
    Used by nurses/CHVs at health facilities
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
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'max': date.today().isoformat()  # Can't be born in future
            }),
            'national_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'National ID (optional)'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254712345678'
            }),
            'alternate_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254798765432 (optional)'
            }),
            'county': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'County'
            }),
            'sub_county': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Sub-County'
            }),
            'ward': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ward'
            }),
            'village': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Village/Estate (optional)'
            }),
            'next_of_kin_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Full Name (optional)'
            }),
            'next_of_kin_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+254712345678 (optional)'
            }),
            'next_of_kin_relationship': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Husband, Sister, Mother'
            }),
        }
    
    def clean_date_of_birth(self):
        """Validate date of birth - must be at least 12 years old"""
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            today = date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            
            if age < 12:
                raise ValidationError('Mother must be at least 12 years old.')
            if age > 60:
                raise ValidationError('Please verify the date of birth. Age appears too high.')
            
        return dob
    
    def clean_phone_number(self):
        """Validate and format phone number"""
        phone = self.cleaned_data.get('phone_number')
        if phone:
            # Remove spaces and dashes
            phone = phone.replace(' ', '').replace('-', '')
            
            # Ensure it starts with +254
            if phone.startswith('0'):
                phone = '+254' + phone[1:]
            elif phone.startswith('254'):
                phone = '+' + phone
            elif not phone.startswith('+254'):
                phone = '+254' + phone
            
        return phone


class PregnancyRegistrationForm(forms.ModelForm):
    """
    Form for registering a new pregnancy for an existing mother
    Automatically calculates EDD from LMP
    """
    
    class Meta:
        model = Pregnancy
        fields = [
            'pregnancy_number',
            'parity',
            'lmp',
            'risk_level',
            'risk_factors',
            'previous_csection',
            'previous_complications',
            'notes',
        ]
        widgets = {
            'pregnancy_number': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': '1 (for first pregnancy)'
            }),
            'parity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0 (for first pregnancy)'
            }),
            'lmp': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'max': date.today().isoformat()
            }),
            'risk_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'risk_factors': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter any risk factors: High BP, diabetes, age >35, previous complications, etc.'
            }),
            'previous_csection': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'previous_complications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe any previous pregnancy or delivery complications'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes (optional)'
            }),
        }
        help_texts = {
            'pregnancy_number': 'Total number of pregnancies including current (Gravida)',
            'parity': 'Number of previous deliveries (0 for first-time mothers)',
            'lmp': 'First day of last menstrual period - EDD will be calculated automatically',
        }
    
    def __init__(self, *args, **kwargs):
        self.mother = kwargs.pop('mother', None)
        super().__init__(*args, **kwargs)
        
        # Auto-fill pregnancy number if mother is provided
        if self.mother:
            next_pregnancy_number = self.mother.total_pregnancies + 1
            self.fields['pregnancy_number'].initial = next_pregnancy_number
            
            # Set parity from mother's total pregnancies
            # (parity = pregnancies - 1, since current pregnancy hasn't been delivered)
            if next_pregnancy_number > 1:
                self.fields['parity'].initial = next_pregnancy_number - 1
    
    def clean_lmp(self):
        """Validate LMP date"""
        lmp = self.cleaned_data.get('lmp')
        if lmp:
            today = date.today()
            
            # LMP cannot be in the future
            if lmp > today:
                raise ValidationError('Last Menstrual Period cannot be in the future.')
            
            # LMP should not be more than 42 weeks ago (reasonable pregnancy duration)
            max_lmp = today - timedelta(weeks=42)
            if lmp < max_lmp:
                raise ValidationError(
                    'LMP is more than 42 weeks ago. Please verify the date or '
                    'consider if delivery has already occurred.'
                )
            
            # Calculate EDD and show it as info
            edd = lmp + timedelta(days=280)
            weeks = (today - lmp).days // 7
            
            # Add helpful message (will be displayed after form validation)
            self.edd_preview = {
                'edd': edd,
                'weeks': weeks,
                'trimester': 1 if weeks <= 12 else (2 if weeks <= 26 else 3)
            }
        
        return lmp
    
    def clean(self):
        """Cross-field validation"""
        cleaned_data = super().clean()
        pregnancy_number = cleaned_data.get('pregnancy_number')
        parity = cleaned_data.get('parity')
        
        # Parity validation
        if pregnancy_number and parity is not None:
            if parity >= pregnancy_number:
                raise ValidationError({
                    'parity': 'Parity (previous deliveries) must be less than pregnancy number.'
                })
            
            # For first pregnancy, parity must be 0
            if pregnancy_number == 1 and parity != 0:
                raise ValidationError({
                    'parity': 'For first pregnancy (G1), parity must be 0 (P0).'
                })
        
        return cleaned_data


class MotherSearchForm(forms.Form):
    """
    Form for searching mothers by name, phone, or ID
    """
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by name, phone, or ID...'
        })
    )
    
    facility = forms.ChoiceField(
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    county = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Filter by county'
        })
    )
    
    has_active_pregnancy = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'All Mothers'),
            ('yes', 'With Active Pregnancy'),
            ('no', 'Without Active Pregnancy')
        ],
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )


class PregnancyUpdateForm(forms.ModelForm):
    """
    Form for updating existing pregnancy details
    LMP and EDD are read-only (use new pregnancy if LMP was wrong)
    """
    
    class Meta:
        model = Pregnancy
        fields = [
            'risk_level',
            'risk_factors',
            'status',
            'notes',
        ]
        widgets = {
            'risk_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'risk_factors': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3
            }),
        }