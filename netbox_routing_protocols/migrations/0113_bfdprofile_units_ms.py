import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('netbox_routing_protocols', '0112_bfdprofile_repair_zero_timers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bfdprofile',
            name='min_tx_int',
            field=models.PositiveIntegerField(
                help_text='Milliseconds. RFC 5880 section 4.1 (Desired Min TX Interval) gives this interval in microseconds: 300 ms here is 300000 in the RFC.',
                validators=[
                    django.core.validators.MinValueValidator(60),
                    django.core.validators.MaxValueValidator(60000),
                ],
                verbose_name='Min TX Interval (ms)',
            ),
        ),
        migrations.AlterField(
            model_name='bfdprofile',
            name='min_rx_int',
            field=models.PositiveIntegerField(
                help_text='Milliseconds. RFC 5880 section 4.1 (Required Min RX Interval) gives this interval in microseconds: 300 ms here is 300000 in the RFC.',
                validators=[
                    django.core.validators.MinValueValidator(60),
                    django.core.validators.MaxValueValidator(60000),
                ],
                verbose_name='Min RX Interval (ms)',
            ),
        ),
        migrations.AlterField(
            model_name='bfdprofile',
            name='multiplier',
            field=models.PositiveSmallIntegerField(
                help_text='Detect Mult (RFC 5880 section 4.1): consecutive packets that may be lost before the session is down. Detection time = multiplier x negotiated interval.',
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(255),
                ],
                verbose_name='Multiplier',
            ),
        ),
    ]
