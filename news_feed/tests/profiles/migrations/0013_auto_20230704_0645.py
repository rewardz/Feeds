# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nominations', '0005_auto_20230704_0645'),
        ('profiles', '0012_customuser_hide_appreciation'),
    ]

    operations = [
        migrations.AddField(
            model_name='trophybadge',
            name='nomination_category',
            field=models.ForeignKey(related_name='badges', blank=True, to='nominations.NominationCategory', null=True),
        ),
        migrations.AddField(
            model_name='trophybadge',
            name='reviewer_level',
            field=models.SmallIntegerField(default=0, help_text='Set it if Nomination Category is selected'),
        ),
    ]
