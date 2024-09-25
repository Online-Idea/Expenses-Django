from django import template
from django.contrib.auth.models import Group


register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_names):
    """
    Проверяет есть ли у пользователя нужные группы, можно несколько, разделённых запятой, пример:
    {% if request.user|has_group:"admin,client" %}
    :param user: пользователь как request.user
    :param group_names: имена групп
    :return:
    """
    groups = Group.objects.filter(name__in=group_names.split(','))
    return any(group in user.groups.all() for group in groups)
