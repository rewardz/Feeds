# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0003_pendingemail_pushnotification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pushnotification',
            name='object_type',
            field=models.SmallIntegerField(default=0, blank=True, choices=[(1, 'Event'), (4, 'Feeds'), (0, 'Plain'), (2, 'Reward'), (3, 'Survey')]),
        ),
    ]
