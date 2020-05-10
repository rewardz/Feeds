# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0005_auto_20200508_0939'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='mark_delete',
            field=models.BooleanField(default=False),
        ),
    ]
