# Generated by Django 5.2.3 on 2025-07-03 20:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_timetablesource_status'),
    ]

    operations = [
        migrations.DeleteModel(
            name='TimetableEvent',
        ),
    ]
