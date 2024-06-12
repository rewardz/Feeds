# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0031_auto_20240110_0544'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='priority',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]
