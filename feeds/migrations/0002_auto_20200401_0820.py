# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import cropimg.fields


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='images',
            name='image',
            field=cropimg.fields.CIImageField(null=True, upload_to=b'post/images/%Y/%m/%d', blank=True),
        ),
    ]
