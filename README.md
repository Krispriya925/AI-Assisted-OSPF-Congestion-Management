## Working OSPF Topology

The current implementation uses Mininet with FRRouting (FRR) to create a small OSPF-enabled network.

### Network Topology

```text
             R2
            /  \
           /    \
         R1------R3
         |        |
        H1        H2
```

### Nodes

* **Routers:** R1, R2, R3
* **Hosts:** H1, H2
* **Routing Protocol:** OSPF
* **Routing Daemon:** FRRouting (FRR)
* **Network Emulator:** Mininet

### IP Addressing

| Device | Interface | IP Address    |
| ------ | --------- | ------------- |
| H1     | h1-eth0   | 10.0.1.1/24   |
| R1     | r1-eth0   | 10.0.1.254/24 |
| R1     | r1-eth1   | 10.0.12.1/24  |
| R2     | r2-eth0   | 10.0.12.2/24  |
| R1     | r1-eth2   | 10.0.13.1/24  |
| R3     | r3-eth0   | 10.0.13.2/24  |
| R2     | r2-eth1   | 10.0.23.1/24  |
| R3     | r3-eth1   | 10.0.23.2/24  |
| R3     | r3-eth2   | 10.0.3.254/24 |
| H2     | h2-eth0   | 10.0.3.1/24   |

### OSPF Router IDs

| Router | Router ID |
| ------ | --------- |
| R1     | 1.1.1.1   |
| R2     | 2.2.2.2   |
| R3     | 3.3.3.3   |

All `10.0.0.0/8` networks are configured in **OSPF Area 0**.

## Working Test Results

The topology was successfully started using:

```bash
sudo python3 ospf_topology.py
```

The routing table on R1 showed an OSPF-learned route to the H2 network:

```text
10.0.3.0/24 nhid 20 via 10.0.13.2 dev r1-eth2 proto ospf metric 20
```

R3 also learned the H1 network through OSPF:

```text
10.0.1.0/24 nhid 24 via 10.0.13.1 dev r3-eth0 proto ospf metric 20
```

### End-to-End Connectivity Test

H1 was able to successfully communicate with H2:

```text
mininet> h1 ping -c 4 h2

PING 10.0.3.1 (10.0.3.1) 56(84) bytes of data.
64 bytes from 10.0.3.1: icmp_seq=1 ttl=62 time=0.711 ms
64 bytes from 10.0.3.1: icmp_seq=2 ttl=62 time=0.093 ms
64 bytes from 10.0.3.1: icmp_seq=3 ttl=62 time=0.139 ms
64 bytes from 10.0.3.1: icmp_seq=4 ttl=62 time=0.117 ms

4 packets transmitted, 4 received, 0% packet loss
rtt min/avg/max/mdev = 0.093/0.265/0.711/0.258 ms
```

**Result:** ✅ End-to-end connectivity between H1 and H2 is working successfully through the OSPF-enabled router network.

## Current Status

* ✅ Mininet topology created
* ✅ R1, R2 and R3 configured
* ✅ H1 and H2 configured
* ✅ FRR Zebra and OSPF daemons running
* ✅ OSPF routes learned successfully
* ✅ H1 → H2 connectivity verified
* ✅ 0% packet loss in the connectivity test
* ⏳ Network monitoring and congestion-data collection are the next stages
