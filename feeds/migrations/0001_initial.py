# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Clap',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('clapped_on', models.DateTimeField(auto_now_add=True)),
                ('clapped_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField()),
                ('commented_on', models.DateTimeField(auto_now_add=True)),
                ('commented_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('parent', models.ForeignKey(related_name='comment_response', blank=True, to='feeds.Comment', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Images',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', models.ImageField(upload_to=b'post/images')),
            ],
        ),
        migrations.CreateModel(
            name='PollsAnswer',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('answer_text', models.CharField(max_length=200)),
                ('votes', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('text', models.TextField(null=True, blank=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('published_date', models.DateTimeField(null=True, blank=True)),
                ('priority', models.BooleanField(default=False)),
                ('prior_till', models.DateTimeField(null=True, blank=True)),
                ('shared_with', models.SmallIntegerField(default=10, choices=[(20, 'All departments'), (10, 'Self department')])),
                ('poll', models.BooleanField(default=False)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('organization', models.ForeignKey(to='profiles.Organization')),
            ],
            options={
                'ordering': ('-pk',),
            },
        ),
        migrations.CreateModel(
            name='PostLiked',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('liked_on', models.DateTimeField(auto_now_add=True)),
                ('liked_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('post', models.ForeignKey(to='feeds.Post')),
            ],
        ),
        migrations.CreateModel(
            name='Videos',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('video', models.FileField(upload_to=b'post/videos')),
                ('post', models.ForeignKey(to='feeds.Post')),
            ],
        ),
        migrations.CreateModel(
            name='Voter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_voted', models.DateTimeField(auto_now_add=True)),
                ('answer', models.ForeignKey(to='feeds.PollsAnswer')),
                ('question', models.ForeignKey(to='feeds.Post')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='pollsanswer',
            name='question',
            field=models.ForeignKey(to='feeds.Post'),
        ),
        migrations.AddField(
            model_name='pollsanswer',
            name='voters',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='feeds.Voter', blank=True),
        ),
        migrations.AddField(
            model_name='images',
            name='post',
            field=models.ForeignKey(to='feeds.Post'),
        ),
        migrations.AddField(
            model_name='comment',
            name='post',
            field=models.ForeignKey(to='feeds.Post'),
        ),
        migrations.AddField(
            model_name='clap',
            name='post',
            field=models.ForeignKey(to='feeds.Post'),
        ),
    ]
