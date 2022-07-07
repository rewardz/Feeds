# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings
import annoying.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profiles', '0006_pushnotification_object_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('points', models.DecimalField(max_digits=12, decimal_places=2, blank=True)),
                ('value', models.PositiveIntegerField(default=0, blank=True)),
                ('context', annoying.fields.JSONField(default='{}', blank=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('is_manually_created', models.BooleanField(default=False)),
                ('message', models.TextField(null=True, blank=True)),
                ('remark', models.TextField(null=True, blank=True)),
                ('expiry_date', models.DateField(null=True, blank=True)),
                ('status', models.SmallIntegerField(default=50, choices=[(30, 'Approved'), (50, 'Auto Approved'), (60, 'Benefit Receipt Pending'), (20, 'Pending'), (40, 'Rejected'), (10, 'n/a')])),
                ('bulk_allocation_id', models.IntegerField(null=True, blank=True)),
                ('creator', models.ForeignKey(related_name='created_transactions', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('department', models.ForeignKey(related_name='transaction_department', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='profiles.Department', null=True)),
                ('organization', models.ForeignKey(related_name='transactions', blank=True, to='profiles.Organization')),
                ('updated_by', models.ForeignKey(related_name='updated_transactions', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('user', models.ForeignKey(related_name='transactions', on_delete=django.db.models.deletion.SET_NULL, blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'ordering': ('-created', '-pk'),
            },
        ),
    ]
