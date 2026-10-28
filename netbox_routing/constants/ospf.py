# Limits and defaults from RFC 2328 (OSPF Version 2).
# Interface output cost: 16-bit metric of a router-LSA link (A.4.2).
OSPF_COST_MIN = 1
OSPF_COST_MAX = 65535

# Interface timers, in seconds. RFC 2328 Appendix C.3 names no formal defaults;
# the defaults are the values it gives for a LAN (hello 10, dead 4 x hello,
# retransmit 5, transmit delay 1).
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

# Route tag: 32 bits (RFC 2328 A.4.5).
OSPF_TAG_MAX = 4294967295

# Cost of the default route an ABR advertises into a stub or NSSA area:
# 24-bit metric (RFC 2328 C.2, StubDefaultCost).
OSPF_STUB_DEFAULT_COST_MIN = 0
OSPF_STUB_DEFAULT_COST_MAX = 16777215

# SPF back-off algorithm, in milliseconds. Defaults: RFC 8405 section 6.
OSPF_SPF_INITIAL_DELAY_DEFAULT = 50
OSPF_SPF_SHORT_DELAY_DEFAULT = 200
OSPF_SPF_LONG_DELAY_DEFAULT = 5000
OSPF_SPF_TIME_TO_LEARN_DEFAULT = 500
OSPF_SPF_HOLDDOWN_DEFAULT = 10000

# LSA origination and arrival limits, in milliseconds. Defaults: RFC 2328
# Appendix B (MinLSInterval is 5 seconds, MinLSArrival is 1 second).
OSPF_LSA_MIN_INTERVAL_DEFAULT = 5000
OSPF_LSA_MIN_ARRIVAL_DEFAULT = 1000

# Graceful restart grace period, in seconds: RFC 3623 appendix B.1 (range
# 1 to 1800, suggested default 120).
OSPF_GRACEFUL_RESTART_PERIOD_MIN = 1
OSPF_GRACEFUL_RESTART_PERIOD_MAX = 1800
OSPF_GRACEFUL_RESTART_PERIOD_DEFAULT = 120

# Percentage of max-lsa at which a warning is logged (not set by an RFC).
OSPF_MAX_LSA_THRESHOLD_MIN = 1
OSPF_MAX_LSA_THRESHOLD_MAX = 100
OSPF_MAX_LSA_THRESHOLD_DEFAULT = 75

# Router priority: 8-bit unsigned integer, 0 means never a designated router
# (RFC 2328 C.3). The RFC names no default; 1 is the usual one.
OSPF_PRIORITY_MIN = 0
OSPF_PRIORITY_MAX = 255
OSPF_PRIORITY_DEFAULT = 1

# Cryptographic authentication Key ID: 8-bit field (RFC 2328 D.3).
OSPF_AUTH_KEY_ID_MIN = 0
OSPF_AUTH_KEY_ID_MAX = 255
