# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-20 09:55
from __future__ import unicode_literals

import json
import six

from django.conf import settings
from django.db import migrations
from django.urls import reverse
from twilio.rest import TwilioRestClient


def migrate_twilio_app(channel):
    """
    Migrates a single Twilio channel to use a channel specific TwiML app with new channel-specific endpoints
    """
    org_config = json.loads(channel.org.config)
    client = TwilioRestClient(org_config['ACCOUNT_SID'], org_config['ACCOUNT_TOKEN'])

    number_sid = channel.bod
    is_short_code = len(channel.address) <= 6

    new_receive_url = "https://" + settings.TEMBA_HOST + reverse('handlers.twilio_handler', args=['receive', channel.uuid])
    new_status_url = "https://" + settings.TEMBA_HOST + reverse('handlers.twilio_handler', args=['status', channel.uuid])
    new_voice_url = "https://" + settings.TEMBA_HOST + reverse('handlers.twilio_handler', args=['voice', channel.uuid])

    new_app = client.applications.create(
        friendly_name="%s/%s" % (settings.TEMBA_HOST.lower(), channel.uuid),
        sms_url=new_receive_url,
        sms_method="POST",
        voice_url=new_voice_url,
        voice_fallback_url="https://" + settings.AWS_BUCKET_DOMAIN + "/voice_unavailable.xml",
        voice_fallback_method='GET',
        status_callback=new_status_url,
        status_callback_method='POST'
    )

    # store new app sid on the channel and clear bod as number sid is now in the channel config
    channel.config = json.dumps({'application_sid': new_app.sid, 'number_sid': number_sid})
    channel.bod = None
    channel.save(update_fields=('config', 'bod'))

    # associate the Twilio number with the new app
    if is_short_code:
        client.sms.short_codes.update(number_sid, sms_url=new_receive_url, sms_method='POST')
    else:
        client.phone_numbers.update(number_sid, sms_application_sid=new_app.sid, voice_application_sid=new_app.sid)

    # cleanup old org-level app
    old_app_sid = org_config.get('APPLICATION_SID')

    if old_app_sid:
        # remove app sid from org config
        del org_config['APPLICATION_SID']
        channel.org.config = json.dumps(org_config)
        channel.org.save(update_fields=('config',))

        # delete the old org-level app
        client.applications.delete(sid=old_app_sid)


def migrate_all_twilio_apps(Channel):
    """
    Migrates all active Twilio channels to use channel specific TwiML apps with new channel-specific endpoints
    """
    twilio_channels = list(Channel.objects.filter(channel_type='T', is_active=True).exclude(org=None).select_related('org'))

    if twilio_channels:
        print("Fetched %d Twilio channels to migrate apps for..." % len(twilio_channels))

    if not settings.IS_PROD:
        if twilio_channels:
            print("Skipping Twilio app migration on non-prod instance")
        return

    for c, channel in enumerate(twilio_channels):
        try:
            channel_config = json.loads(channel.config) if channel.config else {}

            if 'application_sid' in channel_config:
                print(" > Skipping channel %s as it appears to be already migrated" % channel.uuid)
                continue

            migrate_twilio_app(channel)

            print(" > Migrated channel %s for org '%s' (%d/%d)" % (channel.uuid, channel.org.name, (c + 1), len(twilio_channels)))
        except Exception as e:
            print(" ! Error occurred migrating app for channel %s: %s" % (channel.uuid, six.text_type(e)))


def apply_as_migration(apps, schema_editor):
    Channel = apps.get_model('channels', 'Channel')
    migrate_all_twilio_apps(Channel)


def apply_manual():
    from temba.channels.models import Channel
    migrate_all_twilio_apps(Channel)


class Migration(migrations.Migration):

    dependencies = [
        ('channels', '0071_auto_20170614_0915'),
    ]

    operations = [
        migrations.RunPython(apply_as_migration)
    ]
