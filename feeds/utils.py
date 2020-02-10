from __future__ import division, print_function, unicode_literals

from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.utils.module_loading import import_string


from rest_framework import exceptions

from .constants import SHARED_WITH
from .models import Post

DEPARTMENT_MODEL = import_string(settings.DEPARTMENTS_NAME)
ERROR_MESSAGE = "Priority post already exists for user. Set priority to false."

def accessible_posts_by_user(user, organization):
    dept_users = []
    for dept in DEPARTMENT_MODEL.objects.filter(users=user):
        for usr in dept.users.all():
            dept_users.append(usr.id)
    if not dept_users:
        # If user does not belong to any department just show posts created by him
        result = Post.objects.filter(Q(organization=organization,
                                       created_by=user))
    else:
        result = Post.objects.filter(Q(organization=organization, \
                                    shared_with=SHARED_WITH.ALL_DEPARTMENTS) |\
                                 Q(created_by__in=dept_users))
    return result


def validate_priority(data):
    """
    This function checks if there are no other post accessible to the user which
    has priority set to True.
    At a single time only one post can be set as priority
    """
    user = data.get('created_by', None)
    organization = data.get('organization', None)
    priority = data.get('priority', None)
    if priority:
        accessible_posts = accessible_posts_by_user(user, organization)
        priority_posts = accessible_posts.filter(priority=True)
        if priority_posts:
            raise exceptions.ValidationError({"priority": _(ERROR_MESSAGE)})
