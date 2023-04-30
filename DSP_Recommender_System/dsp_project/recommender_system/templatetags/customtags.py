from django import template

register = template.Library()


@register.filter
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists()


@register.filter
def has_group_exact(user, group_name):
    return user.groups.filter(name=group_name).exists()