# Generated by Django 3.0.6 on 2020-05-20 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='movies',
            name='time',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
