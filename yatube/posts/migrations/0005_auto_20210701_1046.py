# Generated by Django 2.2.6 on 2021-07-01 07:46

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0004_comment'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['-created']},
        ),
        migrations.RenameField(
            model_name='comment',
            old_name='creted',
            new_name='created',
        ),
    ]
