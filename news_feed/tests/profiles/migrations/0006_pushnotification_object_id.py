# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0005_auto_20200805_0624'),
    ]

    operations = [
        migrations.AddField(
            model_name='pushnotification',
            name='object_id',
            field=models.PositiveIntegerField(null=True, blank=True),
        ),
    ]
