# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('feeds', '0034_post_users'),
    ]

    operations = [
        migrations.AddField(
            model_name='postcertificaterecord',
            name='user',
            field=models.ForeignKey(related_name='post_certificate_records', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
