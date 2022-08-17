# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0020_remove_post_organization'),
    ]

    operations = [
        migrations.AddField(
            model_name='documents',
            name='comment',
            field=models.ForeignKey(blank=True, to='feeds.Comment', null=True),
        ),
        migrations.AddField(
            model_name='images',
            name='comment',
            field=models.ForeignKey(blank=True, to='feeds.Comment', null=True),
        ),
        migrations.AlterField(
            model_name='documents',
            name='post',
            field=models.ForeignKey(blank=True, to='feeds.Post', null=True),
        ),
        migrations.AlterField(
            model_name='images',
            name='post',
            field=models.ForeignKey(blank=True, to='feeds.Post', null=True),
        ),
    ]
