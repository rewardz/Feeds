# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0002_auto_20200401_0820'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pollsanswer',
            options={'ordering': ('pk',)},
        ),
        migrations.AddField(
            model_name='post',
            name='active_days',
            field=models.SmallIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1), django.core.validators.MaxValueValidator(30)]),
        ),
    ]
