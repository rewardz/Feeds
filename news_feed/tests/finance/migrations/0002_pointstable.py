# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0010_userstrength_message'),
        ('finance', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PointsTable',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('point_source', models.PositiveIntegerField(default=0, choices=[(0, 'Custom'), (1, 'Facility Checkin'), (3, 'Organization Credit'), (4, 'Reward Delivey to Organization'), (5, 'Reward Delivey to User'), (2, 'Reward Redemption'), (6, 'Strengths')])),
                ('alias', models.CharField(help_text="If you selected 'custom' type, please name it here otherwise leave it blank", max_length=100, db_index=True, blank=True)),
                ('points', models.DecimalField(null=True, max_digits=12, decimal_places=4, blank=True)),
                ('slug', models.SlugField(unique=True, null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('organization', models.ForeignKey(blank=True, to='profiles.Organization', null=True)),
            ],
        ),
    ]
