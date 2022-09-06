# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0008_pushnotification_is_viewed'),
    ]

    operations = [
        migrations.CreateModel(
            name='Designation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('organization', models.ForeignKey(to='profiles.Organization')),
            ],
        ),
        migrations.CreateModel(
            name='UserDesignation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('department', models.ForeignKey(blank=True, to='profiles.Department', null=True)),
                ('designation', models.ForeignKey(related_name='user_designations', to='profiles.Designation')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
