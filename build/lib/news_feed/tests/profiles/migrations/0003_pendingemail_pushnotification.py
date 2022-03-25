# -*- coding: utf-8 -*-


from django.db import migrations, models
import cropimg.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0002_customuser_img'),
    ]

    operations = [
        migrations.CreateModel(
            name='PendingEmail',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('to', models.EmailField(max_length=255, verbose_name='Destination Email')),
                ('from_user', models.EmailField(max_length=255, null=True, verbose_name='Sender email', blank=True)),
                ('subject', models.CharField(max_length=255, verbose_name='Email Subject')),
                ('body', models.TextField(verbose_name='Email Body')),
                ('type', models.SmallIntegerField(default=0, blank=True, verbose_name='type', choices=[(0, b'HTML'), (1, b'Text')])),
                ('status', models.PositiveSmallIntegerField(default=0, db_index=True, verbose_name='status', choices=[(0, b'Pending'), (1, b'Error'), (3, b'Sent'), (4, b'Spam'), (5, b'Bounced')])),
                ('remarks', models.TextField(null=True, verbose_name='remarks', blank=True)),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
            ],
            options={
                'verbose_name': 'pending email',
                'verbose_name_plural': 'pending emails',
            },
        ),
        migrations.CreateModel(
            name='PushNotification',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.TextField(help_text=b'You have 255 characters left.', max_length=255, null=True, blank=True)),
                ('image', cropimg.fields.CIImageField(null=True, upload_to=b'notifications/', blank=True)),
                ('object_type', models.SmallIntegerField(default=0, blank=True, choices=[(1, 'Event'), (0, 'Plain'), (2, 'Reward'), (3, 'Survey')])),
                ('state', models.SmallIntegerField(default=0, choices=[(2, 'Delete'), (1, 'Read'), (0, 'Unread')])),
                ('status', models.SmallIntegerField(default=0, choices=[(2, 'Error'), (3, 'Inactive'), (1, 'Sent'), (0, 'Unsent')])),
                ('is_read', models.BooleanField(default=False)),
                ('url', models.URLField(null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('recipient', models.ForeignKey(related_name='recipient', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
                ('sender', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-created',),
                'verbose_name': 'Notification',
                'verbose_name_plural': 'PushNotification',
            },
        ),
    ]
