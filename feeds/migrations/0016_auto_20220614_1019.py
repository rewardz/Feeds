# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0006_pushnotification_object_id'),
        ('feeds', '0015_update_department_m2m_values'),
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
            field=models.ForeignKey(related_name='old_organization', to='profiles.Organization'),
        ),
    ]
