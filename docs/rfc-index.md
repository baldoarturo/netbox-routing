# RFC index

Every standard the plugin refers to, and where it is used. If you know the RFC and want to find the
feature, start here. Vendor features without an RFC are marked as such on the protocol pages.

| RFC | Title (short) | Used for |
| --- | --- | --- |
| [RFC 1195](https://www.rfc-editor.org/rfc/rfc1195) | IS-IS for IP | [IS-IS](protocols/isis.md) |
| [RFC 5302](https://www.rfc-editor.org/rfc/rfc5302) | IS-IS domain-wide prefix distribution (route leaking) | [IS-IS route leaking](protocols/isis.md#route-leaking) |
| [RFC 1765](https://www.rfc-editor.org/rfc/rfc1765) | OSPF database overflow | [OSPF](protocols/ospf.md#limits) |
| [RFC 1793](https://www.rfc-editor.org/rfc/rfc1793) | OSPF demand circuits | [OSPF](protocols/ospf.md#other-interface-options) |
| [RFC 1997](https://www.rfc-editor.org/rfc/rfc1997) | BGP communities (standard, well-known) | [Routing objects](routing-objects.md#communities) |
| [RFC 2328](https://www.rfc-editor.org/rfc/rfc2328) | OSPF version 2 | [OSPF](protocols/ospf.md) |
| [RFC 2385](https://www.rfc-editor.org/rfc/rfc2385) | TCP MD5 signature option | [BGP peers](protocols/bgp.md#peers) |
| [RFC 2973](https://www.rfc-editor.org/rfc/rfc2973) | IS-IS mesh groups | [IS-IS interfaces](protocols/isis.md#interfaces) |
| [RFC 3101](https://www.rfc-editor.org/rfc/rfc3101) | OSPF NSSA | [OSPF areas](protocols/ospf.md#areas), [ranges](protocols/ospf.md#area-ranges) |
| [RFC 3623](https://www.rfc-editor.org/rfc/rfc3623) | OSPF graceful restart | [OSPF instances](protocols/ospf.md#stability-and-maintenance) |
| [RFC 3630](https://www.rfc-editor.org/rfc/rfc3630) | OSPF traffic engineering | [OSPF](protocols/ospf.md#advanced-features) |
| [RFC 3765](https://www.rfc-editor.org/rfc/rfc3765) | NOPEER community | [Routing objects](routing-objects.md#well-known-communities) |
| [RFC 3787](https://www.rfc-editor.org/rfc/rfc3787) | IS-IS recommendations for hello padding | [IS-IS interfaces](protocols/isis.md#interfaces) |
| [RFC 4136](https://www.rfc-editor.org/rfc/rfc4136) | OSPF refresh and flooding reduction | [OSPF interfaces](protocols/ospf.md#other-interface-options) |
| [RFC 4271](https://www.rfc-editor.org/rfc/rfc4271) | BGP-4 | [BGP](protocols/bgp.md), [AS paths](routing-objects.md#as-paths), [Route policies](routing-objects.md#route-policies) (the path attributes they match and set) |
| [RFC 4291](https://www.rfc-editor.org/rfc/rfc4291) | IPv6 addressing | [Prefix lists](routing-objects.md#prefix-lists), [Static routes](protocols/static.md#what-the-plugin-checks) |
| [RFC 4360](https://www.rfc-editor.org/rfc/rfc4360) | BGP extended communities | [Routing objects](routing-objects.md#communities) |
| [RFC 4364](https://www.rfc-editor.org/rfc/rfc4364) | BGP/MPLS VPNs | [BGP](protocols/bgp.md#address-families) |
| [RFC 4632](https://www.rfc-editor.org/rfc/rfc4632) | CIDR | [Prefix lists](routing-objects.md#prefix-lists) |
| [RFC 4659](https://www.rfc-editor.org/rfc/rfc4659) | BGP-MPLS IPv6 VPN | [BGP](protocols/bgp.md#address-families) |
| [RFC 4684](https://www.rfc-editor.org/rfc/rfc4684) | Route-target constrained distribution | [BGP](protocols/bgp.md#address-families) |
| [RFC 4724](https://www.rfc-editor.org/rfc/rfc4724) | BGP graceful restart | [BGP settings](protocols/bgp.md#settings) |
| [RFC 4760](https://www.rfc-editor.org/rfc/rfc4760) | BGP multiprotocol extensions | [BGP address families](protocols/bgp.md#address-families) |
| [RFC 4761](https://www.rfc-editor.org/rfc/rfc4761) | VPLS using BGP | [BGP](protocols/bgp.md#address-families) |
| [RFC 4861](https://www.rfc-editor.org/rfc/rfc4861) | IPv6 neighbor discovery (link-local next hops need an interface) | [Static routes](protocols/static.md#what-the-plugin-checks) |
| [RFC 5082](https://www.rfc-editor.org/rfc/rfc5082) | Generalized TTL security | [BGP peers](protocols/bgp.md#peers), [OSPF interfaces](protocols/ospf.md#other-interface-options) |
| [RFC 5120](https://www.rfc-editor.org/rfc/rfc5120) | IS-IS multi-topology | [IS-IS settings](protocols/isis.md#settings) |
| [RFC 5130](https://www.rfc-editor.org/rfc/rfc5130) | IS-IS administrative tags | [IS-IS interfaces](protocols/isis.md#interfaces), [redistribution](protocols/isis.md#redistribution) |
| [RFC 5250](https://www.rfc-editor.org/rfc/rfc5250) | OSPF opaque LSAs | [OSPF](protocols/ospf.md#advanced-features) |
| [RFC 5286](https://www.rfc-editor.org/rfc/rfc5286) | Loop-free alternates | [OSPF](protocols/ospf.md#areas), [IS-IS](protocols/isis.md#fast-reroute-and-micro-loops) |
| [RFC 5303](https://www.rfc-editor.org/rfc/rfc5303) | IS-IS three-way handshake for point-to-point | [IS-IS interfaces](protocols/isis.md#interfaces) |
| [RFC 5304](https://www.rfc-editor.org/rfc/rfc5304) | IS-IS cryptographic authentication (MD5) | [IS-IS](protocols/isis.md#authentication) |
| [RFC 5305](https://www.rfc-editor.org/rfc/rfc5305) | IS-IS traffic engineering | [IS-IS](protocols/isis.md) |
| [RFC 5308](https://www.rfc-editor.org/rfc/rfc5308) | IS-IS for IPv6 | [IS-IS](protocols/isis.md), [address families](protocols/isis.md#address-families) |
| [RFC 5310](https://www.rfc-editor.org/rfc/rfc5310) | IS-IS generic cryptographic authentication | [IS-IS](protocols/isis.md#authentication) |
| [RFC 5396](https://www.rfc-editor.org/rfc/rfc5396) | Textual representation of AS numbers | [BGP settings](protocols/bgp.md#settings), [AS paths](routing-objects.md#as-paths) |
| [RFC 5443](https://www.rfc-editor.org/rfc/rfc5443) | LDP/IGP synchronization | [OSPF](protocols/ospf.md#advanced-features), [IS-IS settings](protocols/isis.md#settings) |
| [RFC 5668](https://www.rfc-editor.org/rfc/rfc5668) | 4-octet AS extended communities | [Routing objects](routing-objects.md#communities) |
| [RFC 5701](https://www.rfc-editor.org/rfc/rfc5701) | IPv6 address specific extended communities | [Routing objects](routing-objects.md#communities) |
| [RFC 5340](https://www.rfc-editor.org/rfc/rfc5340) | OSPF for IPv6 (OSPFv3) | [OSPF](protocols/ospf.md) |
| [RFC 5709](https://www.rfc-editor.org/rfc/rfc5709) | OSPFv2 HMAC-SHA authentication | [OSPF authentication](protocols/ospf.md#authentication) |
| [RFC 5880](https://www.rfc-editor.org/rfc/rfc5880) | BFD | [BFD](bfd.md) |
| [RFC 5882](https://www.rfc-editor.org/rfc/rfc5882) | Generic application of BFD | [IS-IS interfaces](protocols/isis.md#interfaces) |
| [RFC 5925](https://www.rfc-editor.org/rfc/rfc5925) | TCP authentication option | [BGP peers](protocols/bgp.md#peers) |
| [RFC 6119](https://www.rfc-editor.org/rfc/rfc6119) | IPv6 traffic engineering in IS-IS | [IS-IS settings](protocols/isis.md#settings) |
| [RFC 6232](https://www.rfc-editor.org/rfc/rfc6232) | IS-IS purge originator identification | [IS-IS settings](protocols/isis.md#settings) |
| [RFC 6286](https://www.rfc-editor.org/rfc/rfc6286) | AS-wide unique BGP identifier | [BGP settings](protocols/bgp.md#settings) |
| [RFC 6549](https://www.rfc-editor.org/rfc/rfc6549) | OSPFv2 multi-instance | [OSPF instances](protocols/ospf.md#identity) |
| [RFC 6793](https://www.rfc-editor.org/rfc/rfc6793) | Four-octet AS numbers | [BGP routers](protocols/bgp.md#routers), [AS paths](routing-objects.md#as-paths) |
| [RFC 6860](https://www.rfc-editor.org/rfc/rfc6860) | Hiding transit-only networks | [OSPF interfaces](protocols/ospf.md#other-interface-options), [IS-IS settings](protocols/isis.md#settings) |
| [RFC 6987](https://www.rfc-editor.org/rfc/rfc6987) | OSPF stub router advertisement | [OSPF instances](protocols/ospf.md#stability-and-maintenance) |
| [RFC 7432](https://www.rfc-editor.org/rfc/rfc7432) | BGP MPLS-based Ethernet VPN | [BGP](protocols/bgp.md#address-families) |
| [RFC 7490](https://www.rfc-editor.org/rfc/rfc7490) | Remote LFA | [OSPF](protocols/ospf.md#other-interface-options), [IS-IS](protocols/isis.md#fast-reroute-and-micro-loops) |
| [RFC 7611](https://www.rfc-editor.org/rfc/rfc7611) | ACCEPT_OWN community | [Routing objects](routing-objects.md#well-known-communities) |
| [RFC 7166](https://www.rfc-editor.org/rfc/rfc7166) | OSPFv3 authentication trailer | [OSPF authentication](protocols/ospf.md#authentication) |
| [RFC 7474](https://www.rfc-editor.org/rfc/rfc7474) | OSPF security extension: key rollover lifetimes | [OSPF authentication](protocols/ospf.md#additional-keys-key-rollover) |
| [RFC 7684](https://www.rfc-editor.org/rfc/rfc7684) | OSPFv2 extended prefix/link LSAs | [OSPF](protocols/ospf.md#prefix-sids) |
| [RFC 7752](https://www.rfc-editor.org/rfc/rfc7752) | BGP link-state | [BGP](protocols/bgp.md#address-families) |
| [RFC 7868](https://www.rfc-editor.org/rfc/rfc7868) | EIGRP | [EIGRP](protocols/eigrp.md) |
| [RFC 7911](https://www.rfc-editor.org/rfc/rfc7911) | BGP additional paths | [BGP settings](protocols/bgp.md#settings) |
| [RFC 7999](https://www.rfc-editor.org/rfc/rfc7999) | BLACKHOLE community | [Routing objects](routing-objects.md#well-known-communities) |
| [RFC 8092](https://www.rfc-editor.org/rfc/rfc8092) | BGP large communities | [Routing objects](routing-objects.md#communities) |
| [RFC 8326](https://www.rfc-editor.org/rfc/rfc8326) | Graceful BGP session shutdown | [Routing objects](routing-objects.md#well-known-communities) |
| [RFC 8333](https://www.rfc-editor.org/rfc/rfc8333) | Micro-loop prevention | [IS-IS](protocols/isis.md#fast-reroute-and-micro-loops) |
| [RFC 8349](https://www.rfc-editor.org/rfc/rfc8349) | YANG data model for routing management (static routes, special next hops, route preference) | [Static routes](protocols/static.md) |
| [RFC 8405](https://www.rfc-editor.org/rfc/rfc8405) | SPF back-off delay algorithm | [OSPF](protocols/ospf.md#timers), [IS-IS](protocols/isis.md#timers) |
| [RFC 8667](https://www.rfc-editor.org/rfc/rfc8667) | IS-IS segment routing | [IS-IS](protocols/isis.md#segment-routing), [SR mapping entries](protocols/isis.md#sr-mapping-entries), [adjacency-SIDs](protocols/isis.md#adjacency-sids) |
| [RFC 8661](https://www.rfc-editor.org/rfc/rfc8661) | Segment routing with LDP interworking (mapping server) | [IS-IS SR mapping entries](protocols/isis.md#sr-mapping-entries) |
| [RFC 8570](https://www.rfc-editor.org/rfc/rfc8570) | IS-IS traffic engineering metric extensions (delay) | [IS-IS Flex-Algo](protocols/isis.md#flex-algo) |
| [RFC 8665](https://www.rfc-editor.org/rfc/rfc8665) | OSPF segment routing | [OSPF](protocols/ospf.md#prefix-sids) |
| [RFC 8706](https://www.rfc-editor.org/rfc/rfc8706) | IS-IS restart signaling | [IS-IS settings](protocols/isis.md#settings) |
| [RFC 8955](https://www.rfc-editor.org/rfc/rfc8955), [RFC 8956](https://www.rfc-editor.org/rfc/rfc8956) | BGP Flowspec | [BGP](protocols/bgp.md#address-families) |
| [RFC 8986](https://www.rfc-editor.org/rfc/rfc8986) | SRv6 network programming | [IS-IS SRv6 locators](protocols/isis.md#srv6-locators) |
| [RFC 9026](https://www.rfc-editor.org/rfc/rfc9026) | Multicast VPN fast upstream failover (Standby PE community) | [Routing objects](routing-objects.md#well-known-communities) |
| [RFC 9350](https://www.rfc-editor.org/rfc/rfc9350) | IGP Flexible Algorithm | [IS-IS Flex-Algo](protocols/isis.md#flex-algo) |
| [RFC 9352](https://www.rfc-editor.org/rfc/rfc9352) | IS-IS SRv6 extensions | [IS-IS SRv6 locators](protocols/isis.md#srv6-locators) |
| [RFC 9494](https://www.rfc-editor.org/rfc/rfc9494) | Long-lived graceful restart communities | [Routing objects](routing-objects.md#well-known-communities) |
