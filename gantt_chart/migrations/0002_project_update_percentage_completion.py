# Generated by Django 4.2.1 on 2023-06-08 16:20

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("gantt_chart", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="update_percentage_completion",
            field=models.BooleanField(
                default=False, verbose_name="Обновлять процента выполнения родительским событиям"
            ),
        ),
    ]