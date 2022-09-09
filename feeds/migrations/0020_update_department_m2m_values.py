# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations
from django.utils.module_loading import import_string

from feeds.constants import SHARED_WITH


USER_DEPARTMENT_RELATED_NAME = settings.USER_DEPARTMENT_RELATED_NAME
DEPARTMENT_MODEL = import_string(settings.DEPARTMENT_MODEL)


def update_department_values(apps, schema_editor):
    """
    This function updates the value of the M2M "department" field of each post, based on the
    value of "shared_with" field.
    ex. if shared_with == 10 (SELF_DEPARTMENT), then the department field is updated with only
    the department associated to the created user.
    And if shared_with == 20 (ALL_DEPARTMENTS), then the department field is updated with the
    all the departments available with the organization of the created user
    """
    # get post model
    post_model = apps.get_model("feeds", "Post")

    for post in post_model.objects.filter(mark_delete=False):
        try:
            created_by_user = post.created_by
            if created_by_user:
                if post.shared_with == SHARED_WITH.SELF_DEPARTMENT:
                    user_dept = getattr(created_by_user, USER_DEPARTMENT_RELATED_NAME).all()
                    post.departments.add(*user_dept)
                elif post.shared_with == SHARED_WITH.ALL_DEPARTMENTS:
                    org_depts = DEPARTMENT_MODEL.objects.filter(
                        organization=created_by_user.organization
                    )
                    post.departments.add(*org_depts)
        except Exception as e:
            continue


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0019_post_departments'),
    ]

    operations = [
        migrations.RunPython(update_department_values),
    ]
