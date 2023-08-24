# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0024_auto_20220909_0843'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='shared_with',
            field=models.SmallIntegerField(default=10, choices=[(30, 'Admin only'), (20, 'All departments'), (40, 'Organization departments'), (10, 'Self department')]),
        ),
    ]
