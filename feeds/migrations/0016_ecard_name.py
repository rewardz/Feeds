# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0015_auto_20220530_0805'),
    ]

    operations = [
        migrations.AddField(
            model_name='ecard',
            name='name',
            field=models.CharField(default='abc', max_length=100),
            preserve_default=False,
        ),
    ]
