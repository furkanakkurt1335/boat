# Generated by Django 4.0.3 on 2022-03-26 17:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app1', '0009_alter_sentence_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sentence',
            name='order',
            field=models.PositiveIntegerField(),
        ),
    ]
