# Generated by Django 5.1.2 on 2024-10-19 00:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("arbiter", "0002_remove_policy_query_parameters_alter_policy_query"),
    ]

    operations = [
        migrations.AlterField(
            model_name="policy",
            name="query",
            field=models.JSONField(default=""),
            preserve_default=False,
        ),
    ]
