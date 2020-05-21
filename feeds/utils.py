from __future__ import division, print_function, unicode_literals

from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext as _
from django.utils.module_loading import import_string


from rest_framework import exceptions

from .constants import POST_TYPE, SHARED_WITH
from .models import Post

DEPARTMENT_MODEL = import_string(settings.DEPARTMENT_MODEL)
ERROR_MESSAGE = "Priority post already exists for user. Set priority to false."

def accessible_posts_by_user(user, organization):
    if user.is_superuser:
        result = Post.objects.filter(organization=organization)
        result = result.filter(mark_delete=False)
        return result
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
    result = result.filter(mark_delete=False)
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


def get_departments(user):
    """
    This function returns the department list of a user
    """
    return DEPARTMENT_MODEL.objects.filter(users=user)


def get_profile_image(user):
    """
    This function returns the profile image of the user or none
    """
    profile_image = settings.PROFILE_IMAGE_PROPERTY
    return getattr(user, profile_image, settings.NO_PROFILE_IMAGE)


def user_can_edit(user, instance):
    if instance.post_type == POST_TYPE.USER_CREATED_POLL:
        return False
    if not user.is_staff:
        if instance.post_type == POST_TYPE.SYSTEM_CREATED_POST:
            return False
        return instance.created_by.id == user.id
    return True


def user_can_delete(user, instance):
    if not user.is_staff:
        if instance.post_type in [POST_TYPE.SYSTEM_CREATED_POST]:
            return False
        return instance.created_by.id == user.id
    return True
