# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0026_auto_20221222_0851'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostCertificateRecord',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attachment_type', models.SmallIntegerField(blank=True, null=True, choices=[(2, 'Ecard'), (3, 'Gif'), (1, 'Image')])),
                ('image', models.ForeignKey(blank=True, to='feeds.Images', null=True)),
                ('post', models.ForeignKey(related_name='certificate_records', to='feeds.Post')),
            ],
        ),
    ]
