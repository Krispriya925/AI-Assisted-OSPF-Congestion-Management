from mininet.net import Mininet
from mininet.node import Node
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink


class LinuxRouter(Node):

    def config(self, **params):
        super().config(**params)
        self.cmd("sysctl -w net.ipv4.ip_forward=1")

    def terminate(self):
        self.cmd("sysctl -w net.ipv4.ip_forward=0")
        super().terminate()


def start_ospf(router, router_id):

    info(f"*** Starting FRR/OSPF on {router.name}\n")

    name = router.name
    frr_dir = f"/tmp/frr/{name}"

    router.cmd(f"mkdir -p {frr_dir}")
    router.cmd(f"chown -R frr:frr {frr_dir}")

    zebra_conf = f"""hostname {name}
!
"""

    ospf_conf = f"""hostname {name}
!
router ospf
 ospf router-id {router_id}
 network 10.0.0.0/8 area 0
!
"""

    router.cmd(
        f"cat > {frr_dir}/zebra.conf <<'EOF'\n"
        + zebra_conf +
        "\nEOF"
    )

    router.cmd(
        f"cat > {frr_dir}/ospfd.conf <<'EOF'\n"
        + ospf_conf +
        "\nEOF"
    )

    router.cmd(
        f"chown frr:frr "
        f"{frr_dir}/zebra.conf "
        f"{frr_dir}/ospfd.conf"
    )

    # Start Zebra
    router.cmd(
        f"/usr/lib/frr/zebra "
        f"-d "
        f"-f {frr_dir}/zebra.conf "
        f"-z {frr_dir}/zebra.sock "
        f"-i {frr_dir}/zebra.pid "
        f"--vty_socket {frr_dir} "
        f"--log file:{frr_dir}/zebra.log"
    )

    router.cmd("sleep 1")

    # Start OSPF
    router.cmd(
        f"/usr/lib/frr/ospfd "
        f"-d "
        f"-f {frr_dir}/ospfd.conf "
        f"-z {frr_dir}/zebra.sock "
        f"-i {frr_dir}/ospfd.pid "
        f"--vty_socket {frr_dir} "
        f"--log file:{frr_dir}/ospfd.log"
    )

    info(
        f"*** OSPF started on {name} "
        f"(Router ID {router_id})\n"
    )


def stop_ospf(router):

    name = router.name
    frr_dir = f"/tmp/frr/{name}"

    router.cmd(
        f"[ -f {frr_dir}/ospfd.pid ] && "
        f"kill -9 $(cat {frr_dir}/ospfd.pid) 2>/dev/null"
    )

    router.cmd(
        f"[ -f {frr_dir}/zebra.pid ] && "
        f"kill -9 $(cat {frr_dir}/zebra.pid) 2>/dev/null"
    )


def create_topology():

    net = Mininet(
        controller=None,
        link=TCLink,
        autoSetMacs=True
    )

    # ==================================================
    # ROUTERS
    # ==================================================

    info("*** Adding routers\n")

    r1 = net.addHost(
        "r1",
        cls=LinuxRouter,
        ip=None
    )

    r2 = net.addHost(
        "r2",
        cls=LinuxRouter,
        ip=None
    )

    r3 = net.addHost(
        "r3",
        cls=LinuxRouter,
        ip=None
    )

    r4 = net.addHost(
        "r4",
        cls=LinuxRouter,
        ip=None
    )

    r5 = net.addHost(
        "r5",
        cls=LinuxRouter,
        ip=None
    )

    r6 = net.addHost(
        "r6",
        cls=LinuxRouter,
        ip=None
    )

    # ==================================================
    # HOSTS
    # ==================================================

    info("*** Adding hosts\n")

    h1 = net.addHost(
        "h1",
        ip=None
    )

    h2 = net.addHost(
        "h2",
        ip=None
    )

    # ==================================================
    # LINKS
    # ==================================================

    info("*** Adding links\n")

    # Link configuration
    # Router-to-router links: 10 Mbps
    # Host-to-router links: 100 Mbps

    LINK_BW = 10
    HOST_BW = 100

    # --------------------------------------------------
    # H1 -> R1
    # --------------------------------------------------

    info("*** Adding link: H1 -> R1\n")

    net.addLink(
    h1,
    r1,
    cls=TCLink,
    bw=HOST_BW
    )

    # --------------------------------------------------
    # R1 connections
    # --------------------------------------------------

    info("*** Adding link: R1 -> R2\n")

    net.addLink(
    r1,
    r2,
    cls=TCLink,
    bw=LINK_BW
    )

    info("*** Adding link: R1 -> R3\n")

    net.addLink(
    r1,
    r3,
    cls=TCLink,
    bw=LINK_BW
    )

    info("*** Adding link: R1 -> R6\n")

    net.addLink(
    r1,
    r6,
    cls=TCLink,
    bw=LINK_BW
    )

    # --------------------------------------------------
    # Middle connections
    # --------------------------------------------------
    info("*** Adding link: R2 -> R3\n")

    net.addLink(
    r2,
    r3,
    cls=TCLink,
    bw=LINK_BW
    )

    info("*** Adding link: R2 -> R4\n")

    net.addLink(
    r2,
    r4,
    cls=TCLink,
    bw=LINK_BW
    )

    info("*** Adding link: R3 -> R4\n")

    net.addLink(
    r3,
    r4,
    cls=TCLink,
    bw=LINK_BW
    )

    info("*** Adding link: R3 -> R5\n") 

    net.addLink(
    r3,
    r5,
    cls=TCLink,
    bw=LINK_BW
    )

    # --------------------------------------------------
    # R4 -> R5
    # --------------------------------------------------

    info("*** Adding link: R4 -> R5\n")

    net.addLink(
    r4,
    r5,
    cls=TCLink,
    bw=LINK_BW
    )

    # --------------------------------------------------
    # R6 -> R5
    # --------------------------------------------------

    info("*** Adding link: R6 -> R5\n")

    net.addLink(
    r6,
    r5,
    cls=TCLink,
    bw=LINK_BW
    )

    # --------------------------------------------------
    # R5 -> H2
    # --------------------------------------------------

    info("*** Adding link: R5 -> H2\n")

    net.addLink(
    r5,
    h2,
    cls=TCLink,
    bw=HOST_BW
    )

    # ==================================================
    # START NETWORK
    # ==================================================

    info("*** Starting network\n")

    net.start()

    # ==================================================
    # R1 CONFIGURATION
    # ==================================================

    info("*** Configuring R1\n")

    r1.cmd(
        "ip addr add 10.0.1.254/24 "
        "dev r1-eth0"
    )

    r1.cmd(
        "ip addr add 10.0.12.1/24 "
        "dev r1-eth1"
    )

    r1.cmd(
        "ip addr add 10.0.13.1/24 "
        "dev r1-eth2"
    )

    r1.cmd(
        "ip addr add 10.0.16.1/24 "
        "dev r1-eth3"
    )

    # ==================================================
    # R2 CONFIGURATION
    # ==================================================

    info("*** Configuring R2\n")

    r2.cmd(
        "ip addr add 10.0.12.2/24 "
        "dev r2-eth0"
    )

    r2.cmd(
        "ip addr add 10.0.23.2/24 "
        "dev r2-eth1"
    )

    r2.cmd(
        "ip addr add 10.0.24.1/24 "
        "dev r2-eth2"
    )

    # ==================================================
    # R3 CONFIGURATION
    # ==================================================

    info("*** Configuring R3\n")

    r3.cmd(
        "ip addr add 10.0.13.3/24 "
        "dev r3-eth0"
    )

    r3.cmd(
        "ip addr add 10.0.23.3/24 "
        "dev r3-eth1"
    )

    r3.cmd(
        "ip addr add 10.0.34.3/24 "
        "dev r3-eth2"
    )

    r3.cmd(
        "ip addr add 10.0.35.3/24 "
        "dev r3-eth3"
    )

    # ==================================================
    # R4 CONFIGURATION
    # ==================================================

    info("*** Configuring R4\n")

    r4.cmd(
        "ip addr add 10.0.24.4/24 "
        "dev r4-eth0"
    )

    r4.cmd(
        "ip addr add 10.0.34.4/24 "
        "dev r4-eth1"
    )

    r4.cmd(
        "ip addr add 10.0.45.4/24 "
        "dev r4-eth2"
    )

    # ==================================================
    # R5 CONFIGURATION
    # ==================================================

    info("*** Configuring R5\n")

    r5.cmd(
        "ip addr add 10.0.35.5/24 "
        "dev r5-eth0"
    )

    r5.cmd(
        "ip addr add 10.0.45.5/24 "
        "dev r5-eth1"
    )

    r5.cmd(
        "ip addr add 10.0.56.5/24 "
        "dev r5-eth2"
    )

    r5.cmd(
        "ip addr add 10.0.5.254/24 "
        "dev r5-eth3"
    )

    # ==================================================
    # R6 CONFIGURATION
    # ==================================================

    info("*** Configuring R6\n")

    r6.cmd(
        "ip addr add 10.0.16.6/24 "
        "dev r6-eth0"
    )

    r6.cmd(
        "ip addr add 10.0.56.6/24 "
        "dev r6-eth1"
    )

    # ==================================================
    # H1 CONFIGURATION
    # ==================================================

    info("*** Configuring H1\n")

    h1.cmd(
        "ip addr add 10.0.1.1/24 "
        "dev h1-eth0"
    )

    h1.cmd(
        "ip route add default "
        "via 10.0.1.254"
    )

    # ==================================================
    # H2 CONFIGURATION
    # ==================================================

    info("*** Configuring H2\n")

    h2.cmd(
        "ip addr add 10.0.5.1/24 "
        "dev h2-eth0"
    )

    h2.cmd(
        "ip route add default "
        "via 10.0.5.254"
    )

    # ==================================================
    # START OSPF
    # ==================================================

    info("*** Starting OSPF\n")

    start_ospf(r1, "1.1.1.1")
    start_ospf(r2, "2.2.2.2")
    start_ospf(r3, "3.3.3.3")
    start_ospf(r4, "4.4.4.4")
    start_ospf(r5, "5.5.5.5")
    start_ospf(r6, "6.6.6.6")

    info("*** OSPF topology ready\n")

    # ==================================================
    # MININET CLI
    # ==================================================

    CLI(net)

    # ==================================================
    # STOP OSPF
    # ==================================================

    info("*** Stopping OSPF daemons\n")

    stop_ospf(r1)
    stop_ospf(r2)
    stop_ospf(r3)
    stop_ospf(r4)
    stop_ospf(r5)
    stop_ospf(r6)

    # ==================================================
    # STOP NETWORK
    # ==================================================

    info("*** Stopping network\n")

    net.stop()


if __name__ == "__main__":

    setLogLevel("info")

    create_topology()