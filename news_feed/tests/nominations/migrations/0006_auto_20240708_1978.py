# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('nominations', '0005_auto_20230704_0645'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='nominations',
            name='nominated_team_member',
        ),
    ]
