# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CustomUser',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(null=True, verbose_name='last login', blank=True)),
                ('email', models.EmailField(unique=True, max_length=255)),
                ('first_name', models.CharField(default=b'', max_length=100, blank=True)),
                ('last_name', models.CharField(default=b'', max_length=100, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('date_of_birth', models.DateField(null=True, blank=True)),
                ('wedding_date', models.DateField(null=True, blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('is_admin_staff', models.BooleanField(default=False)),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('employee_id', models.TextField(default=b'', unique=True)),
                ('is_p2p_staff', models.BooleanField(default=False, help_text=b'p2p staff is not limited by p2p_points_limit, but can recognize users in the same org only')),
            ],
            options={
                'verbose_name': 'user',
            },
        ),
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(max_length=200)),
            ],
            options={
                'ordering': ('slug', 'pk'),
            },
        ),
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('slug', models.SlugField(unique=True, db_index=False, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PasswordHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=100, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(related_name='password_history', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Password history entry',
                'verbose_name_plural': 'Password history entries',
            },
        ),
        migrations.AddField(
            model_name='department',
            name='organization',
            field=models.ForeignKey(related_name='departments', to='profiles.Organization'),
        ),
        migrations.AddField(
            model_name='department',
            name='users',
            field=models.ManyToManyField(related_name='departments', to=settings.AUTH_USER_MODEL, blank=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='organization',
            field=models.ForeignKey(related_name='users', to='profiles.Organization'),
        ),
        migrations.AlterUniqueTogether(
            name='department',
            unique_together=set([('organization', 'slug')]),
        ),
    ]
