# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0032_auto_20240611_0957'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='source_language',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='Comment',
            name='source_language',
            field=models.CharField(max_length=100, null=True, blank=True),
        ),
    ]
