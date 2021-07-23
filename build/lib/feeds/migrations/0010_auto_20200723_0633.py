# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0009_flagpost'),
    ]

    operations = [
        migrations.AddField(
            model_name='flagpost',
            name='notified',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='flagpost',
            name='accepted',
            field=models.BooleanField(default=False),
        ),
    ]
