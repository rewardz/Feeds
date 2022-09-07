# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0010_userstrength_message'),
        ('nominations', '0002_nominationcategory_auto_action_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='nominationcategory',
            name='badge',
            field=models.OneToOneField(null=True, blank=True, to='profiles.TrophyBadge'),
        ),
        migrations.AddField(
            model_name='nominations',
            name='message_to_reviewer',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='nominations',
            name='user_strength',
            field=models.ForeignKey(blank=True, to='profiles.UserStrength', null=True),
        ),
    ]
