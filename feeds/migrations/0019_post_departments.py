# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0018_comment_mark_delete'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='departments',
            field=models.ManyToManyField(related_name='posts', to='profiles.Department'),
        ),
    ]
