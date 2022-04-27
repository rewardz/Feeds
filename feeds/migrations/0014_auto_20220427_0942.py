# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import cropimg.fields
import feeds.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profiles', '0006_pushnotification_object_id'),
        ('feeds', '0013_auto_20220309_0543'),
    ]

    operations = [
        migrations.CreateModel(
            name='CommentReportAbuse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reason', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('modified_on', models.DateTimeField(auto_now=True)),
                ('comment', models.ForeignKey(to='feeds.Comment')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ECard',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', cropimg.fields.CIImageField(null=True, upload_to=feeds.models.post_upload_to_path, blank=True)),
                ('img_large', cropimg.fields.CIThumbnailField(size=(1, 1), max_length=30, null=True, image_field=b'image', blank=True)),
                ('img_display', cropimg.fields.CIThumbnailField(size=(1, 1), max_length=30, null=True, image_field=b'image', blank=True)),
                ('img_thumbnail', cropimg.fields.CIThumbnailField(size=(1, 1), max_length=30, null=True, image_field=b'image', blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ECardCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('organization', models.ForeignKey(to='profiles.Organization')),
            ],
        ),
        migrations.CreateModel(
            name='PostReportAbuse',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('reason', models.TextField()),
                ('is_active', models.BooleanField(default=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('modified_on', models.DateTimeField(auto_now=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='commentliked',
            name='reaction_type',
            field=models.SmallIntegerField(default=0, choices=[(1, 'Celebrate'), (5, 'Curious'), (4, 'Insightful'), (0, 'Like'), (3, 'Love'), (2, 'Support')]),
        ),
        migrations.AddField(
            model_name='post',
            name='gif',
            field=models.URLField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='post',
            name='transaction',
            field=models.ForeignKey(blank=True, to='finance.Transaction', null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='user',
            field=models.ForeignKey(related_name='appreciated_user', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
        migrations.AddField(
            model_name='postliked',
            name='reaction_type',
            field=models.SmallIntegerField(default=0, choices=[(1, 'Celebrate'), (5, 'Curious'), (4, 'Insightful'), (0, 'Like'), (3, 'Love'), (2, 'Support')]),
        ),
        migrations.AlterField(
            model_name='post',
            name='post_type',
            field=models.SmallIntegerField(default=1, choices=[(5, 'Most appreciated'), (4, 'Most liked'), (3, 'System created post'), (6, 'User created appreciation'), (2, 'User created poll'), (1, 'User created post')]),
        ),
        migrations.AddField(
            model_name='postreportabuse',
            name='post',
            field=models.ForeignKey(to='feeds.Post'),
        ),
        migrations.AddField(
            model_name='postreportabuse',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='ecard',
            name='category',
            field=models.ForeignKey(to='feeds.ECardCategory'),
        ),
        migrations.AddField(
            model_name='post',
            name='ecard',
            field=models.ForeignKey(blank=True, to='feeds.ECard', null=True),
        ),
    ]
