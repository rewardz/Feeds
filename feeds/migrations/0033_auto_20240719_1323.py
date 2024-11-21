# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0032_auto_20240611_0957'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='transaction',
        ),
    ]
