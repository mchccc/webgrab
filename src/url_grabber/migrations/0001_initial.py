# Generated by Django 2.2.1 on 2019-05-06 18:14

from django.db import migrations, models
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TaskDetails',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(db_index=True, default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(db_index=True, default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('address', models.URLField(db_index=True)),
                ('started', models.BooleanField(default=False)),
                ('completed', models.BooleanField(default=False)),
                ('status_code', models.IntegerField(null=True)),
                ('error', models.CharField(max_length=1024, null=True)),
                ('image_file', models.ImageField(null=True, upload_to='screenshots')),
                ('image_download_datetime', models.DateTimeField(null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
