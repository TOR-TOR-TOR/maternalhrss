from django.contrib import admin
from django.utils.html import format_html
from .models import Delivery, Baby

@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = [
        'mother_name',
        'delivery_date_time',
        'delivery_type',
        'outcome_display',
        'number_of_babies',
        'gestational_age',
        'facility'
    ]
    
    list_filter = [
        'delivery_type',
        'delivery_outcome',
        'delivery_date',
        'facility',
    ]
    
    search_fields = [
        'pregnancy__mother__first_name',
        'pregnancy__mother__last_name',
    ]
    
    readonly_fields = [
        'gestational_age_at_delivery',
        'is_preterm',
        'is_term',
        'is_postterm',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Pregnancy Information', {
            'fields': ('pregnancy',)
        }),
        ('Delivery Details', {
            'fields': (
                'delivery_date',
                'delivery_time',
                'delivery_type',
                'delivery_outcome',
                'number_of_babies',
            )
        }),
        ('Gestational Age', {
            'fields': (
                'gestational_age_at_delivery',
                'is_preterm',
                'is_term',
                'is_postterm',
            ),
            'classes': ('collapse',)
        }),
        ('Mother\'s Condition', {
            'fields': (
                'mother_condition',
                'complications',
                'blood_loss_ml',
                'placenta_complete',
                'placenta_weight_grams',
            ),
            'classes': ('collapse',)
        }),
        ('Facility & Staff', {
            'fields': (
                'facility',
                'attended_by',
            )
        }),
        ('Notes', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
    )
    
    def mother_name(self, obj):
        return obj.mother.full_name
    mother_name.short_description = 'Mother'
    
    def delivery_date_time(self, obj):
        return f"{obj.delivery_date} {obj.delivery_time.strftime('%H:%M')}"
    delivery_date_time.short_description = 'Date & Time'
    
    def outcome_display(self, obj):
        colors = {
            'LIVE': 'green',
            'STILLBIRTH': 'red',
            'NEONATAL_DEATH': 'red',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.delivery_outcome, 'black'),
            obj.get_delivery_outcome_display()
        )
    outcome_display.short_description = 'Outcome'
    
    def gestational_age(self, obj):
        ga = obj.gestational_age_at_delivery
        if ga:
            # Ensure ga is an integer
            ga_value = int(ga) if ga else 0
            
            if obj.is_preterm:
                color = 'orange'
                label = 'Preterm'
            elif obj.is_postterm:
                color = 'red'
                label = 'Postterm'
            else:
                color = 'green'
                label = 'Term'
            return format_html(
                '<span>{} weeks (<span style="color: {};">{}</span>)</span>',
                ga_value, color, label
            )
        return '-'
    gestational_age.short_description = 'GA'


@admin.register(Baby)
class BabyAdmin(admin.ModelAdmin):
    list_display = [
        'display_name_formatted',
        'gender',
        'mother_name',
        'birth_date',
        'age_display',
        'weight_display',
        'apgar_display',
        'facility',
    ]
    
    list_filter = [
        'gender',
        'delivery__delivery_date',
        'facility',
    ]
    
    search_fields = [
        'first_name',
        'mother__first_name',
        'mother__last_name',
    ]
    
    readonly_fields = [
        'age_in_days',
        'age_in_weeks',
        'age_in_months',
        'weight_category',
        'created_at',
        'updated_at',
    ]
    
    fieldsets = (
        ('Baby Details', {
            'fields': (
                'first_name',
                'middle_name',
                'last_name',
                'gender',
                'birth_order',
            )
        }),
        ('Links', {
            'fields': (
                'delivery',
                'mother',
            )
        }),
        ('Birth Measurements', {
            'fields': (
                'birth_weight_grams',
                'weight_category',
                'birth_length_cm',
                'head_circumference_cm',
            )
        }),
        ('APGAR Scores', {
            'fields': (
                'apgar_score_1min',
                'apgar_score_5min',
            )
        }),
        ('Health Information', {
            'fields': (
                'health_condition',
                'complications',
                'required_resuscitation',
            ),
            'classes': ('collapse',)
        }),
        ('Age Information', {
            'fields': (
                'age_in_days',
                'age_in_weeks',
                'age_in_months',
            ),
            'classes': ('collapse',)
        }),
        ('Facility & Registration', {
            'fields': (
                'facility',
                'registered_by',
                'birth_notification_number',
            )
        }),
    )
    
    def display_name_formatted(self, obj):
        icon = '♂' if obj.gender == 'M' else '♀'
        color = '#2196F3' if obj.gender == 'M' else '#E91E63'
        # Convert to string to ensure it's not a SafeString
        name = str(obj.display_name) if obj.display_name else ''
        return format_html(
            '<span style="color: {};">{} {}</span>',
            color, icon, name
        )
    display_name_formatted.short_description = 'Name'
    
    def mother_name(self, obj):
        return obj.mother.full_name
    mother_name.short_description = 'Mother'
    
    def birth_date(self, obj):
        return obj.delivery.delivery_date
    birth_date.short_description = 'Birth Date'
    
    def age_display(self, obj):
        return obj.get_age_display()
    age_display.short_description = 'Age'
    
    def weight_display(self, obj):
        # Handle case where birth_weight_grams might be None
        if not obj.birth_weight_grams:
            return '-'
        
        # Calculate weight directly from the field, not from the property
        weight_grams = obj.birth_weight_grams  # This is an IntegerField
        weight_kg = weight_grams / 1000.0
        
        # Format the number FIRST, then pass as string to format_html
        weight_formatted = f"{weight_kg:.2f}"
        
        # Determine color based on low birth weight status
        color = 'red' if weight_grams < 2500 else 'green'
        
        return format_html(
            '<span style="color: {};">{} kg</span>',
            color, weight_formatted
        )
    weight_display.short_description = 'Birth Weight'
    
    def apgar_display(self, obj):
        if obj.apgar_score_1min and obj.apgar_score_5min:
            return f"{obj.apgar_score_1min} / {obj.apgar_score_5min}"
        return '-'
    apgar_display.short_description = 'APGAR (1/5)'