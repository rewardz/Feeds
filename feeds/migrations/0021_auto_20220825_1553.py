# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forward(apps, schema_editor):
    Post = apps.get_model("feeds", "Post")
    for post in Post.objects.all():
        post.organizations.add(post.organization)


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0020_auto_20220825_1552'),
    ]

    operations = [
        migrations.RunPython(forward)
    ]
