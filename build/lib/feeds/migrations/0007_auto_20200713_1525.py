# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0006_post_mark_delete'),
    ]

    operations = [
        migrations.RenameField(
            model_name='commentliked',
            old_name='post',
            new_name='comment',
        ),
    ]
