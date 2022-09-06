# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0017_auto_20220813_0951'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='departments',
            field=models.ManyToManyField(related_name='posts', to='profiles.Department'),
        ),
    ]
