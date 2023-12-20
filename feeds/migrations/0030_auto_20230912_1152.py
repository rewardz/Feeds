# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0238_customuser_show_dependent_details'),
        ('feeds', '0029_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='post',
            name='job_families',
            field=models.ManyToManyField(related_name='posts', to='profiles.UserJobFamily'),
        ),
        migrations.AlterField(
            model_name='post',
            name='shared_with',
            field=models.SmallIntegerField(default=10, choices=[(30, 'Admin only'), (20, 'All departments'), (40, 'Organization departments'), (10, 'Self department'), (50, 'Self job family')]),
        ),
    ]
