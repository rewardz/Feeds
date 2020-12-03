# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('feeds', '0010_auto_20200723_0633'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentTaggedUsers',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('tagged_on', models.DateTimeField(auto_now_add=True)),
                ('comment', models.ForeignKey(to='feeds.Comment')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='comment',
            name='tagged_users',
            field=models.ManyToManyField(related_name='comment_tagged_users', through='feeds.CommentTaggedUsers', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
