# Generated by Django 4.0.3 on 2023-01-26 13:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20190620_1359'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='customuser',
            options={'ordering': ('last_name', 'last_name_2', 'first_name')},
        ),
    ]