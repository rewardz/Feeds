# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nominations', '0004_auto_20230509_1222'),
    ]

    operations = [
        migrations.RenameField(
            model_name='nominationcategory',
            old_name='reviewer_levels',
            new_name='reviewer_level',
        ),
        migrations.RemoveField(
            model_name='nominationcategory',
            name='badges',
        ),
        migrations.AlterField(
            model_name='nominations',
            name='nom_status',
            field=models.SmallIntegerField(default=0, choices=[(3, 'Approved'), (1, 'In review approver1'), (2, 'In review approver2'), (4, 'Rejected'), (0, 'Submitted')]),
        ),
    ]
