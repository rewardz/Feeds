# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('feeds', '0004_auto_20200416_1513'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='modified_by',
            field=models.ForeignKey(related_name='comment_modifier', to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='comment',
            name='modified_on',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='modified_by',
            field=models.ForeignKey(related_name='post_modifier', to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='modified_on',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
