# Generated by Django 4.0.4 on 2022-04-24 09:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('webapp', '0002_alter_paper_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='journal',
            name='name',
            field=models.CharField(max_length=1000, unique=True),
        ),
        migrations.AlterField(
            model_name='organization',
            name='name',
            field=models.CharField(max_length=1000, unique=True),
        ),
    ]