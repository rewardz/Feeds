# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0011_auto_20201130_1017'),
    ]

    operations = [
        migrations.AddField(
            model_name='postliked',
            name='reaction_type',
            field=models.PositiveIntegerField(default=0, verbose_name='user reaction type', choices=[(0, 'Celebrate'), (1, 'Curious'), (2, 'Insightful'), (3, 'Like'), (4, 'Love'), (5, 'Support')]),
        ),
    ]
