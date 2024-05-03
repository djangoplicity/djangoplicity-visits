from django import template
from djangoplicity.visits.utils import obfuscate_email, obfuscate_phone  # Asegúrate de importar las funciones correctamente

register = template.Library()


@register.filter(name='obfuscate_email')
def obfuscate_email_filter(email):
    return obfuscate_email(email)


@register.filter(name='obfuscate_phone')
def obfuscate_phone_filter(phone):
    return obfuscate_phone(phone)
