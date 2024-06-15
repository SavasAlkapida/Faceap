from django import template
from django.forms.widgets import TextInput

register = template.Library()

@register.filter(name='addclass')
def addclass(value, arg):
    if isinstance(value.field.widget, TextInput):
        value.field.widget.attrs['class'] = value.field.widget.attrs.get('class', '') + ' ' + arg
    return value
