# Generated by Django 2.0.8 on 2018-10-12 15:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("flows", "0181_flowsession_timeout_on")]

    operations = [migrations.AddField(model_name="flowrun", name="parent_uuid", field=models.UUIDField(null=True))]
