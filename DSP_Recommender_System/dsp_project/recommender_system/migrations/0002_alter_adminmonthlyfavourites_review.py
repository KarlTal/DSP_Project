# Generated by Django 4.1.3 on 2023-04-19 15:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recommender_system', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='adminmonthlyfavourites',
            name='review',
            field=models.TextField(blank=True, null=True),
        ),
    ]
