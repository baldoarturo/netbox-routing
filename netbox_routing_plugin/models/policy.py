from django.db import models
from django.utils.translation import gettext_lazy as _

__all__ = ('RoutePolicyMixin',)


class RoutePolicyMixin(models.Model):
    """
    The import and the export policy of a routing protocol instance, each an optional
    route policy. Import filters the routes the protocol accepts into the routing table;
    export filters the routes the protocol advertises or takes from other sources. A route
    policy in use cannot be deleted (PROTECT).
    """

    import_policy = models.ForeignKey(
        to='netbox_routing_plugin.RoutePolicy',
        on_delete=models.PROTECT,
        related_name='%(class)s_import',
        blank=True,
        null=True,
        verbose_name=_('Import Policy'),
        help_text=_('Route policy that filters the routes the protocol accepts'),
    )
    export_policy = models.ForeignKey(
        to='netbox_routing_plugin.RoutePolicy',
        on_delete=models.PROTECT,
        related_name='%(class)s_export',
        blank=True,
        null=True,
        verbose_name=_('Export Policy'),
        help_text=_(
            'Route policy that filters the routes the protocol advertises or takes '
            'from other sources'
        ),
    )

    class Meta:
        abstract = True
