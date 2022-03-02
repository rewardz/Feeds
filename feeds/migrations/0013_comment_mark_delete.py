# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0012_post_tags'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='mark_delete',
            field=models.BooleanField(default=False),
        ),
    ]
