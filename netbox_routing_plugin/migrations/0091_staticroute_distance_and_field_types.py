import django.core.validators
from django.db import migrations, models


def fix_values(apps, schema_editor):
    StaticRoute = apps.get_model('netbox_routing_plugin', 'StaticRoute')
    StaticRoute.objects.filter(name__isnull=True).update(name='')
    StaticRoute.objects.filter(permanent__isnull=True).update(permanent=False)
    StaticRoute.objects.filter(tag__lt=0).update(tag=None)
    # Distance 0 is not valid on any vendor (RFC 8349 route-preference, IOS 1-255)
    StaticRoute.objects.filter(metric=0).update(metric=1)


class Migration(migrations.Migration):
    dependencies = [
        ('netbox_routing_plugin', '0090_isis_redistribution_summary_leak'),
    ]

    operations = [
        migrations.RunPython(fix_values, migrations.RunPython.noop),
        migrations.RemoveConstraint(
            model_name='staticroute',
            name='metric_gte_lte',
        ),
        migrations.RenameField(
            model_name='staticroute',
            old_name='metric',
            new_name='distance',
        ),
        migrations.AlterField(
            model_name='staticroute',
            name='distance',
            field=models.PositiveSmallIntegerField(
                blank=True,
                default=1,
                help_text='Administrative distance (Junos: preference, RFC 8349: route-preference). Lower wins; 1-255, default 1',
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(255),
                ],
                verbose_name='Distance',
            ),
        ),
        migrations.AlterModelOptions(
            name='staticroute',
            options={'ordering': ['vrf', 'prefix', 'distance', 'pk']},
        ),
        migrations.AddConstraint(
            model_name='staticroute',
            constraint=models.CheckConstraint(
                condition=models.Q(('distance__lte', 255), ('distance__gte', 1)),
                name='staticroute_distance_1_255',
            ),
        ),
        migrations.AlterField(
            model_name='staticroute',
            name='name',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Optional name for this static route',
                max_length=50,
                verbose_name='Name',
            ),
        ),
        migrations.AlterField(
            model_name='staticroute',
            name='permanent',
            field=models.BooleanField(default=False, verbose_name='Permanent'),
        ),
        migrations.AlterField(
            model_name='staticroute',
            name='tag',
            field=models.PositiveBigIntegerField(
                blank=True,
                help_text='Optional tag for this static route (0-4294967295)',
                null=True,
                validators=[django.core.validators.MaxValueValidator(4294967295)],
                verbose_name='Route Tag',
            ),
        ),
    ]
