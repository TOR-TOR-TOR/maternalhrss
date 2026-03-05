# apps/anc/templatetags/anc_extras.py
from django import template

register = template.Library()

@register.filter
def getfield(form, field_name):
    """Return a bound form field by name. Usage: {{ form|getfield:'weight_kg' }}"""
    return form[field_name]