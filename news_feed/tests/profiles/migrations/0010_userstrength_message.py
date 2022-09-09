# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0009_designation_userdesignation'),
    ]

    operations = [
        migrations.AddField(
            model_name='userstrength',
            name='message',
            field=models.TextField(null=True, blank=True),
        ),
    ]
