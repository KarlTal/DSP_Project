# Generated by Django 4.1.3 on 2023-04-22 14:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recommender_system', '0003_book_cover_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='book_library',
            name='private',
            field=models.BooleanField(default=False),
        ),
    ]