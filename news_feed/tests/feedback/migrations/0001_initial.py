# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Feedback',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('status', models.PositiveSmallIntegerField(default=0, db_index=True, choices=[(3, 'Closed'), (4, 'Closed & Awarded'), (5, 'Error'), (1, 'Submitted'), (2, 'Under Review'), (0, 'Unpublished')])),
                ('resolve_date', models.DateTimeField(null=True, blank=True)),
                ('resolved_by', models.ForeignKey(related_name='resolved_feedbacks', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
