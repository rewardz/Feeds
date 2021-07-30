# -*- coding: utf-8 -*-


from django.db import migrations, models
from django.conf import settings
import cropimg.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('content', models.TextField()),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('parent', models.ForeignKey(related_name='comment_response', blank=True, to='feeds.Comment', null=True, on_delete=models.SET_NULL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CommentLiked',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('post', models.ForeignKey(to='feeds.Comment', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Images',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('image', cropimg.fields.CIImageField(null=True, upload_to=b'post/images', blank=True)),
                ('img_large', cropimg.fields.CIThumbnailField(size=(1, 1), max_length=30, null=True, image_field=b'image', blank=True)),
                ('img_display', cropimg.fields.CIThumbnailField(size=(1, 1), max_length=30, null=True, image_field=b'image', blank=True)),
                ('img_thumbnail', cropimg.fields.CIThumbnailField(size=(1, 1), max_length=30, null=True, image_field=b'image', blank=True)),
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
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('title', models.CharField(max_length=200, null=True, blank=True)),
                ('description', models.TextField(null=True, blank=True)),
                ('published_date', models.DateTimeField(null=True, blank=True)),
                ('priority', models.BooleanField(default=False)),
                ('prior_till', models.DateTimeField(null=True, blank=True)),
                ('shared_with', models.SmallIntegerField(default=10, choices=[(20, 'All departments'), (10, 'Self department')])),
                ('post_type', models.SmallIntegerField(default=1, choices=[(3, 'System created post'), (2, 'User created poll'), (1, 'User created post')])),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('organization', models.ForeignKey(to='profiles.Organization', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-pk',),
            },
        ),
        migrations.CreateModel(
            name='PostLiked',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('post', models.ForeignKey(to='feeds.Post', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Videos',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('video', models.FileField(upload_to=b'post/videos')),
                ('post', models.ForeignKey(to='feeds.Post', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Voter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('date_voted', models.DateTimeField(auto_now_add=True)),
                ('answer', models.ForeignKey(to='feeds.PollsAnswer', on_delete=models.CASCADE)),
                ('question', models.ForeignKey(to='feeds.Post', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.AddField(
            model_name='pollsanswer',
            name='question',
            field=models.ForeignKey(to='feeds.Post', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='pollsanswer',
            name='voters',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL, through='feeds.Voter', blank=True),
        ),
        migrations.AddField(
            model_name='images',
            name='post',
            field=models.ForeignKey(to='feeds.Post', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='comment',
            name='post',
            field=models.ForeignKey(to='feeds.Post', on_delete=models.CASCADE),
        ),
    ]
