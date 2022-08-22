# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0015_auto_20220707_0924'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commentliked',
            name='reaction_type',
            field=models.SmallIntegerField(default=0, choices=[(6, 'Applause'), (1, 'Celebrate'), (5, 'Curious'), (4, 'Insightful'), (0, 'Like'), (3, 'Love'), (2, 'Support')]),
        ),
        migrations.AlterField(
            model_name='post',
            name='post_type',
            field=models.SmallIntegerField(default=1, choices=[(5, 'Most appreciated'), (4, 'Most liked'), (3, 'System created post'), (6, 'User created appreciation'), (7, 'User created nomination'), (2, 'User created poll'), (1, 'User created post')]),
        ),
        migrations.AlterField(
            model_name='postliked',
            name='reaction_type',
            field=models.SmallIntegerField(default=0, choices=[(6, 'Applause'), (1, 'Celebrate'), (5, 'Curious'), (4, 'Insightful'), (0, 'Like'), (3, 'Love'), (2, 'Support')]),
        ),
    ]
