# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def migrate_data_for_transactions(apps, schema_editor):
    Post = apps.get_model("feeds", "Post")
    posts = Post.objects.filter(transaction__isnull=False)
    for post in posts.iterator():
        transaction = post.transaction
        if transaction:
            post.transactions.add(transaction)


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0001_initial'),
        ('feeds', '0030_auto_20230912_1152'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='transaction',
            field=models.ForeignKey(related_name='posts', to='finance.Transaction', blank=True, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='transactions',
            field=models.ManyToManyField(to='finance.Transaction', blank=True),
        ),
        migrations.RunPython(migrate_data_for_transactions),
    ]
