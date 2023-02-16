# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0026_auto_20221222_0851'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='greeting',
            field=models.ForeignKey(related_name='posts', blank=True, to='events.RepeatedEvent', null=True),
        ),
    ]
