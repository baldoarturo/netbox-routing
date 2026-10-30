from django.utils.translation import gettext_lazy as _

__all__ = ('source_problem',)

# The IP version of an EIGRP address family is a number, of the others a name
_EIGRP_FAMILY = {'ipv4': 4, 'ipv6': 6}


def source_problem(protocol, source, instance_device_id, instance_vrf_id, family):
    """
    Why a source cannot feed a routing instance (#528), or None. A redistribution is
    per address family: the source is on the device of the instance, in its VRF, and
    runs the IP version of the address family ('ipv4' or 'ipv6').

    protocol is 'bgp', 'ospf', 'isis' or 'eigrp'. The source is the instance, or for
    EIGRP the router (its address families carry the VRF) or an EIGRP address family.
    """
    # imported here: the models import this module
    from netbox_routing_protocols.models import (
        BGPAddressFamily,
        EIGRPAddressFamily,
        EIGRPRouter,
        ISISAddressFamily,
    )
    from netbox_routing_protocols.models.bgp import BGP_FAMILY_OF_AF

    if protocol == 'eigrp' and isinstance(source, EIGRPRouter):
        # an EIGRP router has no VRF: the address family of the VRF is what counts
        device_id, vrf_id = source.device_id, instance_vrf_id

        def supports(version):
            return EIGRPAddressFamily.objects.filter(
                router=source, vrf_id=instance_vrf_id, family=_EIGRP_FAMILY[version]
            ).exists()

    elif protocol == 'eigrp':
        # an EIGRP address family: its router is on the device, the family has the VRF
        device_id, vrf_id = source.router.device_id, source.vrf_id

        def supports(version):
            return source.family == _EIGRP_FAMILY[version]

    elif protocol == 'ospf':
        device_id, vrf_id = source.device_id, source.vrf_id

        def supports(version):
            return source.address_family == version

    elif protocol == 'isis':
        device_id, vrf_id = source.device_id, source.vrf_id

        def supports(version):
            return ISISAddressFamily.objects.filter(
                instance=source, address_family=version
            ).exists()

    else:  # bgp
        device_id, vrf_id = source.device_id, source.vrf_id

        def supports(version):
            names = [name for name, v in BGP_FAMILY_OF_AF.items() if v == version]
            return BGPAddressFamily.objects.filter(
                instance=source, address_family__in=names
            ).exists()

    if device_id != instance_device_id:
        return _('The source must be on the same device as the instance.')
    if vrf_id != instance_vrf_id:
        return _('The source must be in the same VRF as the instance.')
    if not supports(family):
        return _('The source does not run this IP version (%(family)s).') % {
            'family': family
        }
    return None
