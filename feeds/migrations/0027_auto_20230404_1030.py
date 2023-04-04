# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0026_auto_20221222_0851'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ecardcategory',
            name='organization',
            field=models.ForeignKey(blank=True, to='profiles.Organization', null=True),
        ),
    ]
