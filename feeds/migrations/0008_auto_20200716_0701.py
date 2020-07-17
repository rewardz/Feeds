# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('feeds', '0007_auto_20200713_1525'),
    ]

    operations = [
        migrations.CreateModel(
            name='PostTaggedUsers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tagged_on', models.DateTimeField(auto_now_add=True)),
                ('post', models.ForeignKey(to='feeds.Post')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='post',
            name='tagged_users',
            field=models.ManyToManyField(related_name='tagged_users', through='feeds.PostTaggedUsers', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
