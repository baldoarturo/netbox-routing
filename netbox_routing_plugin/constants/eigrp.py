from django.db.models import Q

EIGRP_ROUTER_MODELS = Q(
    app_label='netbox_routing_plugin',
    model__in=(
        'eigrpnamedrouter',
        'eigrpclassicrouter',
    ),
)

EIGRP_ASSIGNABLE_MODELS = Q(
    app_label='netbox_routing_plugin',
    model__in=(
        'eigrpnamedrouter',
        'eigrpclassicrouter',
        'eigrpaddressfamily',
    ),
)
