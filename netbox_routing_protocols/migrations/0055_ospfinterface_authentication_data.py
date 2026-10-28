from django.db import migrations
from django.db.models import F


def split_authentication(apps, schema_editor):
    """
    The passphrase used to hold the key chain name too, and there was no key ID.
    Move the key chain names to their own field and give the message digest keys
    that have none the key ID 1.
    """
    OSPFInterface = apps.get_model('netbox_routing_protocols', 'OSPFInterface')
    OSPFInterface.objects.filter(authentication='key-chain').exclude(
        passphrase__isnull=True
    ).exclude(passphrase='').update(key_chain=F('passphrase'), passphrase=None)
    OSPFInterface.objects.filter(
        authentication='message-digest', authentication_key_id__isnull=True
    ).exclude(passphrase__isnull=True).exclude(passphrase='').update(
        authentication_key_id=1
    )


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_routing_protocols', '0054_ospfinterface_authentication'),
    ]

    operations = [
        migrations.RunPython(split_authentication, migrations.RunPython.noop),
    ]
