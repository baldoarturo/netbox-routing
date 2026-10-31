from django import forms

__all__ = ('InlineRadioSelect',)


class InlineRadioSelect(forms.RadioSelect):
    """
    Radio buttons side by side. NetBox's generic input template gives every input the
    `form-control` class, which stretches a plain RadioSelect into full-width boxes.
    """

    template_name = 'netbox_routing_plugin/widgets/radio.html'
    option_template_name = 'netbox_routing_plugin/widgets/radio_option.html'
