# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def forward(apps, schema_editor):
    Post = apps.get_model("feeds", "Post")
    for post in Post.objects.all():
        post.organizations.add(post.organization)


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0021_auto_20220909_1552'),
    ]

    operations = [
        migrations.RunPython(forward)
    ]
