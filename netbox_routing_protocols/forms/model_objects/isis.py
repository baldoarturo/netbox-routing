# SPDX-License-Identifier: Apache-2.0

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.forms import fields
from django.utils.translation import gettext_lazy as _

from dcim.models import Device, Interface
from ipam.models import VRF
from netbox.forms import PrimaryModelForm
from utilities.forms import BOOLEAN_WITH_BLANK_CHOICES, get_field_value
from utilities.forms.fields import DynamicModelChoiceField
from utilities.forms.rendering import FieldSet, TabbedGroups
from utilities.forms.widgets import HTMXSelect

from netbox_routing_protocols.choices import (
    ISISRedistributionMetricTypeChoices,
    ISISSettingChoices,
)
from netbox_routing_protocols.models import (
    BGPInstance,
    EIGRPRouter,
    OSPFInstance,
    ISISInstance,
    ISISInterface,
    ISISSetting,
    ISISLevel,
    ISISInterfaceLevel,
    ISISSegmentRouting,
    ISISFlexAlgo,
    ISISPrefixSID,
    ISISSRv6Locator,
    ISISAddressFamily,
    ISISSRMappingEntry,
    ISISAdjacencySID,
    ISISAreaAddress,
    ISISRedistribution,
    ISISSummaryAddress,
    ISISRouteLeak,
)
from netbox_routing_protocols.models.objects import RoutePolicy

__all__ = (
    'ISISInstanceForm',
    'ISISInterfaceForm',
    'ISISSettingForm',
    'ISISLevelForm',
    'ISISInterfaceLevelForm',
    'ISISSegmentRoutingForm',
    'ISISFlexAlgoForm',
    'ISISPrefixSIDForm',
    'ISISSRv6LocatorForm',
    'ISISAddressFamilyForm',
    'ISISSRMappingEntryForm',
    'ISISAdjacencySIDForm',
    'ISISAreaAddressForm',
    'ISISRedistributionForm',
    'ISISSummaryAddressForm',
    'ISISRouteLeakForm',
)


class ISISSettingMixin:
    """Inject the EAV settings as inline form fields (mirrors BGPSettingMixin).

    Renders each ISISSettingChoices key as a typed form field seeded from any
    existing ISISSetting row attached to the object, and on save creates /
    updates / deletes the backing ISISSetting rows accordingly.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._append_settings_fields()

    def _append_settings_fields(self):
        fieldsets = list(self.fieldsets)
        setting_fields = []
        # Preload existing settings once — avoids an N+1 query (and a repeated
        # ContentType lookup) per settings key on every form render.
        existing = {}
        if getattr(self, 'instance', None) and self.instance.pk:
            ct = ContentType.objects.get_for_model(self.Meta.model)
            existing = {
                s.key: s.value
                for s in ISISSetting.objects.filter(
                    assigned_object_type=ct, assigned_object_id=self.instance.pk
                )
            }
        for key, label in ISISSettingChoices.CHOICES:
            initial = existing.get(key)
            field_type = ISISSettingChoices.FIELD_TYPES[key]
            if field_type == 'string':
                self.fields[key] = fields.CharField(
                    label=label, required=False, initial=initial, max_length=128
                )
            elif field_type == 'integer':
                self.fields[key] = fields.IntegerField(
                    label=label, required=False, initial=initial, min_value=0
                )
            elif field_type == 'boolean':
                # ISISSetting.clean() accepts textual booleans (true/false/1/0/yes/no) from the
                # API/import paths, but the NullBooleanField select only matches real
                # True/False/None — a raw text initial would render blank and then be deleted on
                # save. Normalize the stored text to a real bool first.
                if isinstance(initial, str):
                    normalized = initial.strip().lower()
                    if normalized in ('true', '1', 'yes'):
                        initial = True
                    elif normalized in ('false', '0', 'no'):
                        initial = False
                    else:
                        initial = None
                choices = (
                    (None, '---------'),
                    (True, _('True')),
                    (False, _('False')),
                )
                if key in ISISSettingChoices.CHECKBOXES:
                    self.fields[key] = fields.BooleanField(
                        label=label, required=False, initial=bool(initial)
                    )
                    self.fields[key].help_text = ISISSettingChoices.HELP_TEXTS.get(
                        key, ''
                    )
                    setting_fields.append(key)
                    continue
                self.fields[key] = fields.NullBooleanField(
                    label=label,
                    required=False,
                    initial=initial,
                    widget=forms.Select(choices=choices),
                )
            self.fields[key].help_text = ISISSettingChoices.HELP_TEXTS.get(key, '')
            css = self.fields[key].widget.attrs.get('class', '')
            self.fields[key].widget.attrs['class'] = f'{css} form-control'
            setting_fields.append(key)

        fieldset = FieldSet(*setting_fields, name=_('Settings'))
        fieldsets.append(fieldset)
        self.fieldsets = fieldsets

    def _persist_isis_settings(self, settings):
        """Upsert / delete the EAV ISISSetting rows for the (now-saved) instance."""
        if not self.instance.pk:
            return
        ct = ContentType.objects.get_for_model(self.instance)
        for key, _name in ISISSettingChoices.CHOICES:
            value = settings.get(key, None)
            setting = ISISSetting.objects.filter(
                assigned_object_type=ct,
                assigned_object_id=self.instance.pk,
                key=key,
            ).first()
            if setting and value not in (None, ''):
                setting.value = value
                setting.clean()
                setting.save()
            elif value not in (None, ''):
                setting = ISISSetting(
                    assigned_object=self.instance,
                    key=key,
                    value=value,
                )
                setting.clean()
                setting.save()
            elif setting:
                setting.delete()

    def save(self, *args, **kwargs):
        commit = args[0] if args else kwargs.get('commit', True)
        settings = {}
        for key, _name in ISISSettingChoices.CHOICES:
            if key in self.cleaned_data:
                settings[key] = self.cleaned_data.pop(key)
        obj = super().save(*args, **kwargs)

        if commit:
            # Object is persisted — upsert the settings immediately.
            self._persist_isis_settings(settings)
        else:
            # commit=False is the NetBox ObjectEditView path: it does
            # form.save(commit=False) -> instance.save() -> form.save_m2m(). The instance
            # has no pk yet, so defer the EAV upsert to save_m2m() (which the view calls
            # after it saves the instance) instead of dropping the submitted settings.
            self._pending_isis_settings = settings
            deferred_save_m2m = self.save_m2m

            def save_m2m():
                deferred_save_m2m()
                self._persist_isis_settings(self._pending_isis_settings)

            self.save_m2m = save_m2m

        return obj


class ISISInstanceForm(ISISSettingMixin, PrimaryModelForm):
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=True,
        selector=True,
        label=_('Device'),
    )
    vrf = DynamicModelChoiceField(
        queryset=VRF.objects.all(),
        required=False,
        selector=True,
        label=_('VRF'),
    )

    import_policy = DynamicModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Import Policy'),
    )
    export_policy = DynamicModelChoiceField(
        queryset=RoutePolicy.objects.all(),
        required=False,
        selector=True,
        label=_('Export Policy'),
    )

    fieldsets = (
        FieldSet('description'),
        FieldSet('device', name=_('Device')),
        FieldSet(
            'vrf', 'process_tag', 'net', 'is_type', 'metric_style', name=_('Instance')
        ),
        FieldSet(
            'overload_bit',
            'overload_on_startup',
            'overload_timeout',
            'suppress_attached_bit',
            'ignore_attached_bit',
            'distance',
            'maximum_paths',
            'reference_bandwidth',
            name=_('Behaviour'),
        ),
        FieldSet(
            'spf_initial_wait',
            'spf_max_wait',
            'lsp_initial_wait',
            'lsp_max_wait',
            'lsp_lifetime',
            'lsp_refresh_interval',
            'lsp_mtu',
            name=_('Timers'),
        ),
        FieldSet('import_policy', 'export_policy', name=_('Route Policy')),
        FieldSet('te_enabled', name=_('Traffic Engineering')),
        FieldSet('fast_reroute', 'microloop_avoidance', name=_('Fast Reroute')),
        FieldSet(
            'area_auth_type',
            'area_auth_key',
            'area_auth_key_id',
            'area_auth_key_chain',
            'area_auth_send_only',
            'domain_auth_type',
            'domain_auth_key',
            'domain_auth_key_id',
            'domain_auth_key_chain',
            'domain_auth_send_only',
            name=_('Authentication'),
        ),
    )

    class Meta:
        model = ISISInstance
        fields = (
            'device',
            'vrf',
            'process_tag',
            'net',
            'is_type',
            'metric_style',
            'import_policy',
            'export_policy',
            'overload_bit',
            'overload_on_startup',
            'overload_timeout',
            'suppress_attached_bit',
            'ignore_attached_bit',
            'distance',
            'maximum_paths',
            'reference_bandwidth',
            'spf_initial_wait',
            'spf_max_wait',
            'lsp_initial_wait',
            'lsp_max_wait',
            'lsp_lifetime',
            'lsp_refresh_interval',
            'lsp_mtu',
            'te_enabled',
            'fast_reroute',
            'microloop_avoidance',
            'area_auth_type',
            'area_auth_key',
            'area_auth_key_id',
            'area_auth_key_chain',
            'area_auth_send_only',
            'domain_auth_type',
            'domain_auth_key',
            'domain_auth_key_id',
            'domain_auth_key_chain',
            'domain_auth_send_only',
            'description',
            'comments',
            'tags',
            'owner',
        )
        widgets = {
            'overload_bit': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'overload_on_startup': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'suppress_attached_bit': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'ignore_attached_bit': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'te_enabled': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'microloop_avoidance': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
        }


class ISISInterfaceForm(ISISSettingMixin, PrimaryModelForm):
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        selector=True,
        label=_('Device'),
    )
    instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
        query_params={'device_id': '$device'},
    )
    interface = DynamicModelChoiceField(
        queryset=Interface.objects.all(),
        required=True,
        selector=True,
        label=_('Interface'),
        query_params={'device_id': '$device'},
    )

    fieldsets = (
        FieldSet('description'),
        FieldSet('device', 'instance', name=_('Instance')),
        FieldSet(
            'interface',
            'address_family',
            'circuit_type',
            'network_type',
            'metric',
            'passive',
            'bfd_enabled',
            'frr_enabled',
            'frr_protection',
            name=_('Interface'),
        ),
        FieldSet(
            'csnp_interval',
            'retransmit_interval',
            'lsp_interval',
            'mesh_group',
            name=_('Timers'),
        ),
        FieldSet(
            'hello_padding',
            'ldp_sync',
            'prefix_suppression',
            'three_way_handshake',
            'admin_group',
            'te_metric',
            'delay_metric',
            'route_tag',
            name=_('Options'),
        ),
        FieldSet(
            'hello_auth_type',
            'hello_auth_key',
            'hello_auth_key_id',
            'hello_auth_key_chain',
            'hello_auth_send_only',
            name=_('Authentication'),
        ),
    )

    class Meta:
        model = ISISInterface
        fields = (
            'device',
            'instance',
            'interface',
            'address_family',
            'circuit_type',
            'network_type',
            'metric',
            'passive',
            'bfd_enabled',
            'frr_enabled',
            'frr_protection',
            'csnp_interval',
            'retransmit_interval',
            'lsp_interval',
            'mesh_group',
            'hello_padding',
            'ldp_sync',
            'prefix_suppression',
            'route_tag',
            'three_way_handshake',
            'admin_group',
            'te_metric',
            'delay_metric',
            'hello_auth_type',
            'hello_auth_key',
            'hello_auth_key_id',
            'hello_auth_key_chain',
            'hello_auth_send_only',
            'description',
            'comments',
            'tags',
            'owner',
        )
        widgets = {
            'passive': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'bfd_enabled': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'frr_enabled': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if (
            self.instance.pk
            and self.instance.interface
            and self.instance.interface.device
        ):
            self.initial['device'] = self.instance.interface.device.pk

    # The instance/interface same-device rule lives on ISISInterface.clean() (model
    # layer), which the form runs via full_clean and which flags both fields — so no
    # form-level clean() override is needed here.


class ISISSettingForm(PrimaryModelForm):
    isisinstance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=False,
        selector=True,
        label=_('Instance'),
    )
    isisinterface = DynamicModelChoiceField(
        queryset=ISISInterface.objects.all(),
        required=False,
        selector=True,
        label=_('Interface'),
    )
    key = forms.ChoiceField(
        choices=ISISSettingChoices,
        required=True,
        label=_('Setting Name'),
    )
    value = forms.CharField(
        required=True,
        label=_('Setting Value'),
    )

    fieldsets = (
        FieldSet(
            TabbedGroups(
                FieldSet('isisinstance', name=_('Instance')),
                FieldSet('isisinterface', name=_('Interface')),
            ),
            name=_('Assigned Object'),
        ),
        FieldSet('key', 'value', name=_('Settings')),
    )

    class Meta:
        model = ISISSetting
        fields = [
            'isisinstance',
            'isisinterface',
            'key',
            'value',
            'description',
            'comments',
            'tags',
            'owner',
        ]

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        # Django permits initial=None; normalize before copying so an explicit
        # initial=None caller doesn't hit AttributeError on NoneType.copy().
        initial = (kwargs.get('initial') or {}).copy()
        if instance and instance.assigned_object:
            if isinstance(instance.assigned_object, ISISInstance):
                initial['isisinstance'] = instance.assigned_object
            elif isinstance(instance.assigned_object, ISISInterface):
                initial['isisinterface'] = instance.assigned_object
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def clean(self):
        super().clean()
        selected = [
            field
            for field in ('isisinstance', 'isisinterface')
            if self.cleaned_data.get(field)
        ]
        if len(selected) > 1:
            raise forms.ValidationError(
                {
                    selected[1]: _(
                        'An IS-IS Setting can only be assigned to a single object.'
                    )
                }
            )
        elif selected:
            self.instance.assigned_object = self.cleaned_data[selected[0]]
        else:
            raise ValidationError(_('An IS-IS Setting must be assigned to an object.'))


class ISISLevelForm(PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )

    fieldsets = (
        FieldSet('description'),
        FieldSet('instance', 'level', name=_('Level')),
        FieldSet(
            'default_metric',
            'wide_metrics_only',
            'preference',
            'labeled_preference',
            'disabled',
            name=_('Attributes'),
        ),
        FieldSet(
            'auth_type',
            'auth_key',
            'auth_key_id',
            'auth_key_chain',
            'auth_send_only',
            name=_('Authentication'),
        ),
    )

    class Meta:
        model = ISISLevel
        fields = (
            'instance',
            'level',
            'default_metric',
            'wide_metrics_only',
            'preference',
            'labeled_preference',
            'disabled',
            'auth_type',
            'auth_key',
            'auth_key_id',
            'auth_key_chain',
            'auth_send_only',
            'description',
            'comments',
            'tags',
            'owner',
        )
        widgets = {
            'wide_metrics_only': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'disabled': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
        }


class ISISInterfaceLevelForm(PrimaryModelForm):
    interface = DynamicModelChoiceField(
        queryset=ISISInterface.objects.all(),
        required=True,
        selector=True,
        label=_('Interface'),
    )

    fieldsets = (
        FieldSet('description'),
        FieldSet('interface', 'level', name=_('Level')),
        FieldSet(
            'metric',
            'hello_interval',
            'hello_multiplier',
            'priority',
            'passive',
            name=_('Attributes'),
        ),
        FieldSet(
            'hello_auth_type',
            'hello_auth_key',
            'hello_auth_key_id',
            'hello_auth_key_chain',
            'hello_auth_send_only',
            name=_('Authentication'),
        ),
    )

    class Meta:
        model = ISISInterfaceLevel
        fields = (
            'interface',
            'level',
            'metric',
            'hello_interval',
            'hello_multiplier',
            'priority',
            'passive',
            'hello_auth_type',
            'hello_auth_key',
            'hello_auth_key_id',
            'hello_auth_key_chain',
            'hello_auth_send_only',
            'description',
            'comments',
            'tags',
            'owner',
        )
        widgets = {'passive': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES)}


class ISISSegmentRoutingForm(PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )

    fieldsets = (
        FieldSet('description'),
        FieldSet('instance', 'enabled', 'srv6_enabled', name=_('Segment Routing')),
        FieldSet(
            'prefix_sid_range',
            'srgb_start',
            'srgb_range',
            'srlb_start',
            'srlb_range',
            'maximum_sid_depth',
            'tunnel_table_pref',
            name=_('Attributes'),
        ),
    )

    class Meta:
        model = ISISSegmentRouting
        fields = (
            'instance',
            'enabled',
            'srv6_enabled',
            'prefix_sid_range',
            'srgb_start',
            'srgb_range',
            'srlb_start',
            'srlb_range',
            'maximum_sid_depth',
            'tunnel_table_pref',
            'description',
            'comments',
            'tags',
            'owner',
        )
        widgets = {
            'enabled': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'srv6_enabled': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
        }


class ISISFlexAlgoForm(PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )

    fieldsets = (
        FieldSet('description'),
        FieldSet('instance', 'algo_id', name=_('Flex-Algo')),
        FieldSet('metric_type', 'priority', name=_('Definition')),
        FieldSet(
            'admin_group_exclude',
            'admin_group_include_any',
            'admin_group_include_all',
            name=_('Affinity'),
        ),
    )

    class Meta:
        model = ISISFlexAlgo
        fields = (
            'instance',
            'algo_id',
            'metric_type',
            'priority',
            'admin_group_exclude',
            'admin_group_include_any',
            'admin_group_include_all',
            'description',
            'comments',
            'tags',
            'owner',
        )


class ISISPrefixSIDForm(PrimaryModelForm):
    interface = DynamicModelChoiceField(
        queryset=ISISInterface.objects.all(),
        required=True,
        selector=True,
        label=_('Interface'),
    )

    fieldsets = (
        FieldSet('description'),
        FieldSet('interface', 'algorithm', name=_('Prefix-SID')),
        FieldSet(
            'sid_index',
            'sid_label',
            'n_flag',
            'no_php',
            'explicit_null',
            'readvertise',
            name=_('Attributes'),
        ),
    )

    class Meta:
        model = ISISPrefixSID
        fields = (
            'interface',
            'algorithm',
            'sid_index',
            'sid_label',
            'n_flag',
            'no_php',
            'explicit_null',
            'readvertise',
            'description',
            'comments',
            'tags',
            'owner',
        )
        widgets = {
            'n_flag': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'no_php': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'explicit_null': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'readvertise': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
        }


class ISISSRv6LocatorForm(PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )

    fieldsets = (
        FieldSet('description'),
        FieldSet('instance', 'name', 'prefix', 'enabled', name=_('SRv6 Locator')),
        FieldSet(
            'algorithm',
            'is_anycast',
            'is_micro_segment',
            'flavor',
            'isis_level',
            name=_('Behaviour'),
        ),
        FieldSet(
            'block_length',
            'node_length',
            'function_length',
            'argument_length',
            name=_('SID structure'),
        ),
        FieldSet('vendor_ext', name=_('Vendor Extensions')),
    )

    class Meta:
        model = ISISSRv6Locator
        fields = (
            'instance',
            'name',
            'prefix',
            'enabled',
            'algorithm',
            'is_anycast',
            'is_micro_segment',
            'flavor',
            'isis_level',
            'block_length',
            'node_length',
            'function_length',
            'argument_length',
            'vendor_ext',
            'description',
            'comments',
            'tags',
            'owner',
        )
        widgets = {
            'is_anycast': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'is_micro_segment': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
            'enabled': forms.Select(choices=BOOLEAN_WITH_BLANK_CHOICES),
        }


class ISISRedistributionForm(PrimaryModelForm):
    # Only used to narrow the instance and the sources to one device; the model
    # validates that the source really is on the instance's device.
    device = DynamicModelChoiceField(
        queryset=Device.objects.all(),
        required=False,
        selector=True,
        label=_('Device'),
    )
    instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
        query_params={'device_id': '$device'},
    )
    ospf_source = DynamicModelChoiceField(
        queryset=OSPFInstance.objects.all(),
        required=False,
        selector=True,
        label=_('OSPF Source'),
        query_params={'device_id': '$device'},
    )
    eigrp_source = DynamicModelChoiceField(
        queryset=EIGRPRouter.objects.all(),
        required=False,
        selector=True,
        label=_('EIGRP Source'),
        query_params={'device_id': '$device'},
    )
    bgp_source = DynamicModelChoiceField(
        queryset=BGPInstance.objects.all(),
        required=False,
        selector=True,
        label=_('BGP Source'),
        help_text=_('A BGP router assigned to the device'),
    )
    isis_source = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=False,
        selector=True,
        label=_('IS-IS Source'),
        query_params={'device_id': '$device'},
    )

    fieldsets = (
        FieldSet(
            'device',
            'instance',
            'address_family',
            'protocol',
            'description',
            name=_('Redistribution'),
        ),
        FieldSet(
            'ospf_source',
            'eigrp_source',
            'bgp_source',
            'isis_source',
            name=_('Source'),
        ),
        FieldSet(
            'level',
            'metric',
            'metric_type',
            'route_tag',
            'route_policy',
            name=_('Attributes'),
        ),
    )

    class Meta:
        model = ISISRedistribution
        widgets = {
            'protocol': HTMXSelect(),
        }
        fields = (
            'device',
            'instance',
            'address_family',
            'protocol',
            'ospf_source',
            'eigrp_source',
            'bgp_source',
            'isis_source',
            'level',
            'metric',
            'metric_type',
            'route_tag',
            'route_policy',
            'description',
            'comments',
            'tags',
            'owner',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.initial['device'] = self.instance.instance.device_id
        # An empty metric type falls back to its default (see clean()).
        self.fields['metric_type'].required = False

        # Only the source of the selected protocol is shown (none for connected,
        # static or while no protocol is selected)
        protocol = get_field_value(self, 'protocol')
        for source_protocol, field in ISISRedistribution.SOURCE_FIELDS.items():
            if source_protocol != protocol:
                del self.fields[field]

    def clean(self):
        if not self.cleaned_data.get('metric_type'):
            self.cleaned_data['metric_type'] = (
                ISISRedistributionMetricTypeChoices.INTERNAL
            )
        # A source left over from a previous protocol is not on the form anymore
        for field in ISISRedistribution.SOURCE_FIELDS.values():
            if field not in self.fields:
                setattr(self.instance, field, None)
        return super().clean()


class ISISSummaryAddressForm(PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )

    fieldsets = (
        FieldSet(
            'instance',
            'prefix',
            'level',
            'not_advertise',
            'metric',
            'route_tag',
            'description',
            name=_('Summary Address'),
        ),
    )

    class Meta:
        model = ISISSummaryAddress
        fields = (
            'instance',
            'prefix',
            'level',
            'not_advertise',
            'metric',
            'route_tag',
            'description',
            'comments',
            'tags',
            'owner',
        )


class ISISRouteLeakForm(PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )

    fieldsets = (
        FieldSet(
            'instance',
            'address_family',
            'route_policy',
            'description',
            name=_('Route Leak'),
        ),
    )

    class Meta:
        model = ISISRouteLeak
        fields = (
            'instance',
            'address_family',
            'route_policy',
            'description',
            'comments',
            'tags',
            'owner',
        )


class ISISAreaAddressForm(PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )

    fieldsets = (FieldSet('instance', 'net', 'description', name=_('Area Address')),)

    class Meta:
        model = ISISAreaAddress
        fields = (
            'instance',
            'net',
            'description',
            'comments',
            'tags',
            'owner',
        )


class ISISSRMappingEntryForm(PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )

    fieldsets = (
        FieldSet(
            'instance',
            'prefix',
            'range_size',
            'description',
            name=_('Mapping Entry'),
        ),
        FieldSet('sid_index', 'sid_label', 'algorithm', 'level', name=_('SID')),
    )

    class Meta:
        model = ISISSRMappingEntry
        fields = (
            'instance',
            'prefix',
            'range_size',
            'sid_index',
            'sid_label',
            'algorithm',
            'level',
            'description',
            'comments',
            'tags',
            'owner',
        )


class ISISAdjacencySIDForm(PrimaryModelForm):
    interface = DynamicModelChoiceField(
        queryset=ISISInterface.objects.all(),
        required=True,
        selector=True,
        label=_('Interface'),
    )

    fieldsets = (
        FieldSet(
            'interface',
            'sid_label',
            'protected',
            'description',
            name=_('Adjacency-SID'),
        ),
    )

    class Meta:
        model = ISISAdjacencySID
        fields = (
            'interface',
            'sid_label',
            'protected',
            'description',
            'comments',
            'tags',
            'owner',
        )


class ISISAddressFamilyForm(PrimaryModelForm):
    instance = DynamicModelChoiceField(
        queryset=ISISInstance.objects.all(),
        required=True,
        selector=True,
        label=_('Instance'),
    )

    fieldsets = (
        FieldSet('instance', 'address_family', 'description', name=_('Address Family')),
        FieldSet(
            'metric_style',
            'distance',
            'maximum_paths',
            'default_originate',
            name=_('Settings'),
        ),
    )

    class Meta:
        model = ISISAddressFamily
        fields = (
            'instance',
            'address_family',
            'metric_style',
            'distance',
            'maximum_paths',
            'default_originate',
            'description',
            'comments',
            'tags',
            'owner',
        )
