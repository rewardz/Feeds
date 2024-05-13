# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('feeds', '0033_auto_20240418_0715'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='users',
            field=models.ManyToManyField(related_name='appreciated_posts', null=True, to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
