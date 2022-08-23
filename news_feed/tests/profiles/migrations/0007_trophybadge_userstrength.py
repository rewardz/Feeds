# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0006_pushnotification_object_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrophyBadge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('icon', models.ImageField(upload_to='trophy_badges/')),
                ('background_color', models.CharField(max_length=20, null=True, blank=True)),
                ('background_color_lite', models.CharField(max_length=20, null=True, blank=True)),
                ('points', models.DecimalField(null=True, max_digits=12, decimal_places=2, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserStrength',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(unique=True, null=True, blank=True)),
                ('icon', models.ImageField(upload_to='profiles/strength/icons')),
                ('illustration', models.ImageField(null=True, upload_to='profiles/strength/illustrations', blank=True)),
                ('background_color', models.CharField(max_length=20, null=True, blank=True)),
                ('background_color_lite', models.CharField(max_length=20, null=True, blank=True)),
                ('organization', models.ForeignKey(blank=True, to='profiles.Organization', null=True)),
            ],
        ),
    ]
