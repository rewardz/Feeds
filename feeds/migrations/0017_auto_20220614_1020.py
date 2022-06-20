# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def forward(apps, schema_editor):
    Post = apps.get_model("feeds", "Post")
    for post in Post.objects.all():
        post.organizations.add(post.organization)


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0016_auto_20220614_1019'),
    ]

    operations = [
        migrations.RunPython(forward)
    ]
