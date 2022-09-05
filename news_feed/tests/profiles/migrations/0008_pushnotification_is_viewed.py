# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0007_trophybadge_userstrength'),
    ]

    operations = [
        migrations.AddField(
            model_name='pushnotification',
            name='is_viewed',
            field=models.BooleanField(default=False, editable=False),
        ),
    ]
