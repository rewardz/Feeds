# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0006_pushnotification_object_id'),
        ('feeds', '0011_auto_20201130_1017'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='organizations',
            field=models.ManyToManyField(related_name='posts', to='profiles.Organization'),
        ),
        migrations.AlterField(
            model_name='post',
            name='organization',
            field=models.ForeignKey(related_name='post', to='profiles.Organization'),
        ),
    ]
