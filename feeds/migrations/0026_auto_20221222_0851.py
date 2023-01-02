# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0001_initial'),
        ('feeds', '0025_auto_20221107_1107'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='greeting',
            field=models.ForeignKey(blank=True, to='events.RepeatedEvent', null=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='post_type',
            field=models.SmallIntegerField(default=1, choices=[(8, 'Feedback post'), (9, 'Greeting message'), (5, 'Most appreciated'), (4, 'Most liked'), (3, 'System created post'), (6, 'User created appreciation'), (7, 'User created nomination'), (2, 'User created poll'), (1, 'User created post')]),
        ),
    ]
