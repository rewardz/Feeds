# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nominations', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='nominationcategory',
            name='auto_action_time',
            field=models.PositiveIntegerField(help_text='Auto Action Time in Hours', null=True, blank=True),
        ),
    ]
