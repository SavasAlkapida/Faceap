from django import template

register = template.Library()

@register.filter(name='addclass')
def addclass(value, arg):
    return value.as_widget(attrs={'class': arg})


register = template.Library()


@register.filter
def add(value, arg):
    return str(value) + str(arg)    

register = template.Library()


@register.filter
def get_attr(obj, attr_name):
    return getattr(obj, attr_name, None)

@register.filter(name='euro_format')
def euro_format(value):
    """
    Değeri Euro formatına çevirir. Örneğin: 12345.67 -> '12.345,67 €'
    """
    try:
        value = float(value)
        return f"{value:,.2f} €".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return value


@register.filter(name='first_image')
def first_image(image_urls):
    """
    Virgülle ayrılmış resim URL'lerinden ilkini döndürür.
    """
    if not image_urls:
        return ""
    return image_urls.split(',')[0].strip()    