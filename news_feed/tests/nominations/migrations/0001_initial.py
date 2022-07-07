# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profiles', '0006_pushnotification_object_id'),
    ]

    operations = [
        migrations.CreateModel(
            name='NominationCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=250, verbose_name='Category Name')),
                ('img', models.ImageField(upload_to='nominations/icon')),
                ('slug', models.SlugField(unique=True, null=True, blank=True)),
                ('end_date', models.DateField()),
                ('nom_cat_order', models.PositiveSmallIntegerField(default=0, help_text='Nomination category will be displayed based on the order')),
                ('limit', models.PositiveSmallIntegerField(default=0, help_text='Limit of users that can be nominated in the same category')),
                ('reviewer_levels', models.SmallIntegerField(default=0, choices=[(1, 'Level1'), (2, 'Level2'), (0, 'None')])),
                ('department', models.ManyToManyField(related_name='nominations_categories_department', to='profiles.Department')),
                ('organization', models.ManyToManyField(related_name='nominations_categories_organization', to='profiles.Organization')),
            ],
        ),
        migrations.CreateModel(
            name='Nominations',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('nom_status', models.SmallIntegerField(default=0, choices=[(3, 'Approved'), (1, 'In review approver1'), (2, 'In review approver2'), (0, 'None'), (4, 'Rejected')])),
                ('comment', models.TextField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('assigned_reviewer', models.ManyToManyField(related_name='reviewer', to=settings.AUTH_USER_MODEL)),
                ('category', models.ForeignKey(related_name='categories', to='nominations.NominationCategory')),
                ('nominated_team_member', models.ForeignKey(related_name='nominated_user', verbose_name='Nominated Team Member', to=settings.AUTH_USER_MODEL)),
                ('nominator', models.ForeignKey(related_name='current_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
