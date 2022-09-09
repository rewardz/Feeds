# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0022_auto_20220909_1553'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='organization',
        ),
    ]
