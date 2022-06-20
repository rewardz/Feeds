# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0017_auto_20220614_1020'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='post',
            name='organization',
        ),
    ]
