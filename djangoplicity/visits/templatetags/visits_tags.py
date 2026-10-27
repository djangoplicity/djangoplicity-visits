from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from djangoplicity.visits.utils import obfuscate_email, obfuscate_phone  # Asegúrate de importar las funciones correctamente

register = template.Library()


@register.filter(name='obfuscate_email')
def obfuscate_email_filter(email):
    return obfuscate_email(email)


@register.filter(name='obfuscate_phone')
def obfuscate_phone_filter(phone):
    return obfuscate_phone(phone)


@register.filter(name='print_line_break')
def print_line_break(text, separator='/'):
    '''
    Add a line break after the first separator, only shown when printing (see .print-only in the template).
    Can be chained to add more than one line break
    '''
    return mark_safe(conditional_escape(text).replace(separator, separator + '<br class="print-only">', 1))
