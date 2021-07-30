# -*- coding: utf-8 -*-


from django.db import migrations, models
import cropimg.fields
import feeds.models


class Migration(migrations.Migration):

    dependencies = [
        ('feeds', '0003_auto_20200414_1304'),
    ]

    operations = [
        migrations.CreateModel(
            name='Documents',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('document', models.FileField(null=True, upload_to=feeds.models.post_upload_to_path, blank=True)),
                ('post', models.ForeignKey(to='feeds.Post', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AlterField(
            model_name='images',
            name='image',
            field=cropimg.fields.CIImageField(null=True, upload_to=feeds.models.post_upload_to_path, blank=True),
        ),
        migrations.AlterField(
            model_name='videos',
            name='video',
            field=models.FileField(upload_to=feeds.models.post_upload_to_path),
        ),
    ]
