# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0027_auto_20230216_0338'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ecardcategory',
            name='organization',
            field=models.ForeignKey(blank=True, to='profiles.Organization', null=True),
        ),
    ]
