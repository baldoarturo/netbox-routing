# Limits and defaults from RFC 2328 (OSPF Version 2).
# Interface output cost: 16-bit metric of a router-LSA link (A.4.2).
OSPF_COST_MIN = 1
OSPF_COST_MAX = 65535

# Interface timers, in seconds. Defaults: RFC 2328 Appendix C.3.
# Hello and dead intervals are limited by their packet field widths
# (16 and 32 bits, A.3.2). Retransmit interval and transmit delay are capped
# at 16 bits, as is the LS age they are compared with.
OSPF_HELLO_INTERVAL_DEFAULT = 10
OSPF_HELLO_INTERVAL_MIN = 1
OSPF_HELLO_INTERVAL_MAX = 65535
OSPF_DEAD_INTERVAL_DEFAULT = 40
OSPF_DEAD_INTERVAL_MIN = 1
OSPF_DEAD_INTERVAL_MAX = 4294967295
OSPF_RETRANSMIT_INTERVAL_DEFAULT = 5
OSPF_RETRANSMIT_INTERVAL_MIN = 1
OSPF_RETRANSMIT_INTERVAL_MAX = 65535
OSPF_TRANSMIT_DELAY_DEFAULT = 1
OSPF_TRANSMIT_DELAY_MIN = 1
OSPF_TRANSMIT_DELAY_MAX = 65535

OSPF_INTERFACE_TIMERS = {
    'hello_interval': (
        OSPF_HELLO_INTERVAL_MIN,
        OSPF_HELLO_INTERVAL_MAX,
        OSPF_HELLO_INTERVAL_DEFAULT,
    ),
    'dead_interval': (
        OSPF_DEAD_INTERVAL_MIN,
        OSPF_DEAD_INTERVAL_MAX,
        OSPF_DEAD_INTERVAL_DEFAULT,
    ),
    'retransmit_interval': (
        OSPF_RETRANSMIT_INTERVAL_MIN,
        OSPF_RETRANSMIT_INTERVAL_MAX,
        OSPF_RETRANSMIT_INTERVAL_DEFAULT,
    ),
    'transmit_delay': (
        OSPF_TRANSMIT_DELAY_MIN,
        OSPF_TRANSMIT_DELAY_MAX,
        OSPF_TRANSMIT_DELAY_DEFAULT,
    ),
}

# External (AS-external-LSA) metric is a 24-bit value; 0xFFFFFF is LSInfinity
# (RFC 2328 A.4.5, 12.4.4).
OSPF_EXTERNAL_METRIC_MIN = 0
OSPF_EXTERNAL_METRIC_MAX = 16777214
