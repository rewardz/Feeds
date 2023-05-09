# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0012_customuser_hide_appreciation'),
        ('nominations', '0003_auto_20220907_0943'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='nominationcategory',
            name='badge',
        ),
        migrations.AddField(
            model_name='nominationcategory',
            name='badges',
            field=models.ManyToManyField(related_name='categories', to='profiles.TrophyBadge', blank=True),
        ),
        migrations.AddField(
            model_name='nominations',
            name='badge',
            field=models.ForeignKey(blank=True, to='profiles.TrophyBadge', null=True),
        ),
        migrations.AddField(
            model_name='nominations',
            name='points',
            field=models.DecimalField(null=True, max_digits=12, decimal_places=2, blank=True),
        ),
    ]
