import django.core.validators
import django.db.models.deletion
import django.db.models.functions.text
from django.core.exceptions import ValidationError
from django.db import migrations, models

from netbox_routing_plugin.helpers.community import parse

SEQUENCE_STEP = 10


def normalise_and_number(apps, schema_editor):
    """
    Give every community its type and normal form (a value that is not a valid community
    is left as it is, and so is one whose normal form is already taken), and number the
    entries of each list in steps of 10 in the order they were shown (by community).
    """
    Community = apps.get_model('netbox_routing_plugin', 'Community')
    CommunityListEntry = apps.get_model('netbox_routing_plugin', 'CommunityListEntry')

    taken = set(Community.objects.values_list('community', flat=True))
    for community in Community.objects.all():
        try:
            kind, value = parse(community.community)
        except ValidationError:
            continue
        if value != community.community and value in taken:
            value = community.community
        taken.discard(community.community)
        taken.add(value)
        Community.objects.filter(pk=community.pk).update(type=kind, community=value)

    # A list takes the type of its communities when they all have the same one
    CommunityList = apps.get_model('netbox_routing_plugin', 'CommunityList')
    for community_list in CommunityList.objects.all():
        kinds = set(
            CommunityListEntry.objects.filter(
                community_list=community_list
            ).values_list('community__type', flat=True)
        )
        if len(kinds) == 1:
            CommunityList.objects.filter(pk=community_list.pk).update(type=kinds.pop())

    last_list, sequence = None, 0
    for entry in CommunityListEntry.objects.order_by(
        'community_list_id', 'community__community', 'pk'
    ):
        if entry.community_list_id != last_list:
            last_list, sequence = entry.community_list_id, 0
        sequence += SEQUENCE_STEP
        CommunityListEntry.objects.filter(pk=entry.pk).update(sequence=sequence)


def check_list_names(apps, schema_editor):
    """The names of the community lists become unique ignoring case: stop with the names to fix"""
    CommunityList = apps.get_model('netbox_routing_plugin', 'CommunityList')
    seen = {}
    for name in CommunityList.objects.order_by('name').values_list('name', flat=True):
        seen.setdefault(name.lower(), []).append(name)
    clashes = [names for names in seen.values() if len(names) > 1]
    if clashes:
        raise RuntimeError(
            'Community list names must be unique ignoring case. Rename these lists '
            'before migrating: ' + '; '.join(' / '.join(names) for names in clashes)
        )


class Migration(migrations.Migration):

    dependencies = [
        ('netbox_routing_plugin', '0082_aspathentry_unique_pattern'),
    ]

    operations = [
        migrations.RunPython(check_list_names, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(name='communitylist', unique_together=set()),
        migrations.AlterModelOptions(
            name='communitylist',
            options={
                'ordering': ['name', 'pk'],
                'verbose_name': 'Community List',
                'verbose_name_plural': 'Community Lists',
            },
        ),
        migrations.AddConstraint(
            model_name='communitylist',
            constraint=models.UniqueConstraint(
                django.db.models.functions.text.Lower('name'),
                name='netbox_routing_plugin_communitylist_unique_name',
                violation_error_message='Name must be unique.',
            ),
        ),
        migrations.AddField(
            model_name='communitylist',
            name='type',
            field=models.CharField(default='standard', max_length=20),
        ),
        migrations.AddField(
            model_name='community',
            name='type',
            field=models.CharField(default='standard', editable=False, max_length=20),
        ),
        migrations.AlterField(
            model_name='community',
            name='community',
            field=models.CharField(max_length=255),
        ),
        migrations.AddField(
            model_name='communitylistentry',
            name='sequence',
            field=models.PositiveBigIntegerField(null=True),
        ),
        migrations.RunPython(normalise_and_number, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='communitylistentry',
            name='sequence',
            field=models.PositiveBigIntegerField(
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(4294967294),
                ]
            ),
        ),
        migrations.AlterField(
            model_name='communitylistentry',
            name='community',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='communitylistentries',
                to='netbox_routing_plugin.community',
            ),
        ),
        migrations.AlterModelOptions(
            name='communitylistentry',
            options={
                'ordering': ('community_list', 'sequence'),
                'verbose_name': 'Community List Entry',
                'verbose_name_plural': 'Community List Entries',
            },
        ),
        migrations.AddConstraint(
            model_name='communitylistentry',
            constraint=models.UniqueConstraint(
                fields=('community_list', 'sequence'),
                name='netbox_routing_plugin_communitylistentry_unique_communitylist_sequence',
                violation_error_message='Community list sequence must be unique.',
            ),
        ),
    ]
