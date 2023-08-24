# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0012_customuser_hide_appreciation'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RepeatedEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('month', models.PositiveSmallIntegerField(default=0, db_index=True, blank=True)),
                ('day', models.PositiveSmallIntegerField(db_index=True)),
                ('year', models.PositiveIntegerField(db_index=True, null=True, blank=True)),
                ('organization', models.ForeignKey(related_name='repeated_events', editable=False, to='profiles.Organization')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-month', '-day', 'id'),
            },
        ),
    ]
