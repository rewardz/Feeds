# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0010_userstrength_message'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuperVisor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('is_approver', models.BooleanField(default=False)),
                ('budget', models.IntegerField(null=True, verbose_name='remaining budget')),
                ('allocated_budget', models.IntegerField(help_text='Initial allocated budget', null=True)),
                ('department', models.ForeignKey(related_name='supervisor', to='profiles.Department', null=True)),
                ('supervisor', models.ForeignKey(related_name='user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
