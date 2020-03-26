# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='img',
            field=models.ImageField(null=True, upload_to=b'user/images', blank=True),
        ),
    ]
