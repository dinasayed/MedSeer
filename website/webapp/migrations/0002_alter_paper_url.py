# Generated by Django 4.0.4 on 2022-04-21 18:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='paper',
            name='url',
            field=models.URLField(blank=True, max_length=1000, null=True, unique=True),
        ),
    ]
