# Generated by Django 4.0.3 on 2022-03-26 17:37

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0007_alter_word_line_head'),
    ]

    operations = [
        migrations.AddField(
            model_name='sentence',
            name='order',
            field=models.PositiveIntegerField(default=1),
            preserve_default=False,
        ),
    ]
