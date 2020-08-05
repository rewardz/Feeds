# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0004_auto_20200805_0621'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pushnotification',
            name='object_type',
            field=models.SmallIntegerField(default=0, blank=True, choices=[(1, 'Event'), (0, 'Plain'), (4, 'Posts'), (2, 'Reward'), (3, 'Survey')]),
        ),
    ]
