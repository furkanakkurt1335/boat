# Generated by Django 4.0.3 on 2022-06-26 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0013_annotation_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='treebank',
            name='language',
            field=models.CharField(default='Turkish', max_length=30),
            preserve_default=False,
        ),
        migrations.AlterUniqueTogether(
            name='sentence',
            unique_together={('sent_id', 'text', 'treebank')},
        ),
    ]
