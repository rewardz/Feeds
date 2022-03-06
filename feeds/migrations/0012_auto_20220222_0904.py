# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0011_auto_20201130_1017'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='post_type',
            field=models.SmallIntegerField(default=1, choices=[(5, 'Most appreciated'), (4, 'Most liked'), (3, 'System created post'), (2, 'User created poll'), (1, 'User created post')]),
        ),
    ]
