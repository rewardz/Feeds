# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def make_many_organizations(apps, schema_editor):
    """
        Adds the Organization object in Post.organization to the
        many-to-many relationship in Post.organizations
    """
    Post = apps.get_model('feeds', 'Post')

    for post in Post.objects.all():
        post.organizations.add(post.organization)


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0012_auto_20210917_0552'),
    ]

    operations = [
        migrations.RunPython(make_many_organizations),
    ]