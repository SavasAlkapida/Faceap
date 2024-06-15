from django import template

register = template.Library()

@register.filter
def euro_format(value):
    try:
        return f"€ {value:.2f}"
    except (ValueError, TypeError):
        return value


@register.filter
def first_image(value):
    if value:
        return value.split(',')[0]
    return value