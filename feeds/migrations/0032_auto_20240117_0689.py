# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0031_auto_20240110_0544'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='transaction',
        ),
    ]
