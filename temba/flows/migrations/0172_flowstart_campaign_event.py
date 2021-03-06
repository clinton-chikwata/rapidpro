# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-08-02 15:52
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("campaigns", "0027_indexes"), ("flows", "0171_fix_path_trigger")]

    operations = [
        migrations.AddField(
            model_name="flowstart",
            name="campaign_event",
            field=models.ForeignKey(
                help_text="The campaign event which created this flow start",
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="flow_starts",
                to="campaigns.CampaignEvent",
            ),
        )
    ]
