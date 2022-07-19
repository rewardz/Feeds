# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0016_ecard_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commentliked',
            name='reaction_type',
            field=models.SmallIntegerField(default=0, choices=[(6, 'Applause'), (1, 'Celebrate'), (5, 'Curious'), (4, 'Insightful'), (0, 'Like'), (3, 'Love'), (2, 'Support')]),
        ),
        migrations.AlterField(
            model_name='postliked',
            name='reaction_type',
            field=models.SmallIntegerField(default=0, choices=[(6, 'Applause'), (1, 'Celebrate'), (5, 'Curious'), (4, 'Insightful'), (0, 'Like'), (3, 'Love'), (2, 'Support')]),
        ),
    ]
