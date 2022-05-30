# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nominations', '0001_initial'),
        ('feeds', '0014_auto_20220505_1133'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='nomination',
            field=models.ForeignKey(blank=True, to='nominations.Nominations', null=True),
        ),
        migrations.AlterField(
            model_name='post',
            name='post_type',
            field=models.SmallIntegerField(default=1, choices=[(5, 'Most appreciated'), (4, 'Most liked'), (3, 'System created post'), (6, 'User created appreciation'), (7, 'User created nomination'), (2, 'User created poll'), (1, 'User created post')]),
        ),
    ]
