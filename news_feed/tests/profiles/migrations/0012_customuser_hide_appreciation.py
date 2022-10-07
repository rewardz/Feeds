# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0011_supervisor'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='hide_appreciation',
            field=models.BooleanField(default=False, help_text='Hide appreciations from other users'),
        ),
    ]
