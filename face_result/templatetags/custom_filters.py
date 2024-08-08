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