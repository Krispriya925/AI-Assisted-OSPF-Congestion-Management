
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

    # Create router-specific directory
    router.cmd(f"mkdir -p {frr_dir}")
    router.cmd(f"chown -R frr:frr {frr_dir}")

    # --------------------------------------------------
    # Zebra configuration
    # --------------------------------------------------

    zebra_conf = f"""hostname {name}
!
"""

    # --------------------------------------------------
    # OSPF configuration
    # --------------------------------------------------

    ospf_conf = f"""hostname {name}
!
router ospf
 ospf router-id {router_id}
 network 10.0.0.0/8 area 0
!
"""

    # Write zebra.conf
    router.cmd(
        f"cat > {frr_dir}/zebra.conf <<'EOF'\n"
        + zebra_conf +
        "\nEOF"
    )

    # Write ospfd.conf
    router.cmd(
        f"cat > {frr_dir}/ospfd.conf <<'EOF'\n"
        + ospf_conf +
        "\nEOF"
    )

    # Give FRR ownership
    router.cmd(f"chown frr:frr {frr_dir}/*.conf")

    # --------------------------------------------------
    # Start Zebra
    # --------------------------------------------------

    router.cmd(
        f"/usr/lib/frr/zebra "
        f"-d "
        f"-N {name} "
        f"-f {frr_dir}/zebra.conf "
        f"-z {frr_dir}/zebra.sock "
        f"-i {frr_dir}/zebra.pid"
    )

    # --------------------------------------------------
    # Start OSPF daemon
    # --------------------------------------------------

    router.cmd(
        f"/usr/lib/frr/ospfd "
        f"-d "
        f"-N {name} "
        f"-f {frr_dir}/ospfd.conf "
        f"-z {frr_dir}/zebra.sock "
        f"-i {frr_dir}/ospfd.pid"
    )

    info(f"*** OSPF started on {name} (Router ID {router_id})\n")


def create_topology():

    # --------------------------------------------------
    # Create Mininet
    # --------------------------------------------------

    net = Mininet(
        controller=None,
        link=TCLink,
        autoSetMacs=True
    )

    info("*** Adding routers\n")

    r1 = net.addHost("r1", cls=LinuxRouter)
    r2 = net.addHost("r2", cls=LinuxRouter)
    r3 = net.addHost("r3", cls=LinuxRouter)

    info("*** Adding hosts\n")

    h1 = net.addHost("h1")
    h2 = net.addHost("h2")

    # --------------------------------------------------
    # Create links
    #
    # Interface order:
    #
    # R1:
    # eth0 -> H1
    # eth1 -> R2
    # eth2 -> R3
    #
    # R2:
    # eth0 -> R1
    # eth1 -> R3
    #
    # R3:
    # eth0 -> R1
    # eth1 -> R2
    # eth2 -> H2
    # --------------------------------------------------

    info("*** Adding links\n")

    net.addLink(h1, r1)
    net.addLink(r1, r2)
    net.addLink(r1, r3)
    net.addLink(r2, r3)
    net.addLink(h2, r3)

    # --------------------------------------------------
    # Start network
    # --------------------------------------------------

    info("*** Starting network\n")

    net.start()

    # --------------------------------------------------
    # Configure R1
    # --------------------------------------------------

    info("*** Configuring R1\n")

    r1.cmd("ip addr add 10.0.1.254/24 dev r1-eth0")
    r1.cmd("ip addr add 10.0.12.1/24 dev r1-eth1")
    r1.cmd("ip addr add 10.0.13.1/24 dev r1-eth2")

    # --------------------------------------------------
    # Configure R2
    # --------------------------------------------------

    info("*** Configuring R2\n")

    r2.cmd("ip addr add 10.0.12.2/24 dev r2-eth0")
    r2.cmd("ip addr add 10.0.23.1/24 dev r2-eth1")

    # --------------------------------------------------
    # Configure R3
    # --------------------------------------------------

    info("*** Configuring R3\n")

    r3.cmd("ip addr add 10.0.13.2/24 dev r3-eth0")
    r3.cmd("ip addr add 10.0.23.2/24 dev r3-eth1")
    r3.cmd("ip addr add 10.0.3.254/24 dev r3-eth2")

    # --------------------------------------------------
    # Configure H1
    # --------------------------------------------------

    info("*** Configuring H1\n")

    h1.cmd("ip addr add 10.0.1.1/24 dev h1-eth0")
    h1.cmd("ip route add default via 10.0.1.254")

    # --------------------------------------------------
    # Configure H2
    # --------------------------------------------------

    info("*** Configuring H2\n")

    h2.cmd("ip addr add 10.0.3.1/24 dev h2-eth0")
    h2.cmd("ip route add default via 10.0.3.254")

    # --------------------------------------------------
    # Start OSPF
    # --------------------------------------------------

    info("*** Starting OSPF\n")

    start_ospf(r1, "1.1.1.1")
    start_ospf(r2, "2.2.2.2")
    start_ospf(r3, "3.3.3.3")

    info("*** OSPF topology ready\n")

    # --------------------------------------------------
    # Start Mininet CLI
    # --------------------------------------------------

    CLI(net)

    # --------------------------------------------------
    # Stop network
    # --------------------------------------------------

    info("*** Stopping network\n")

    net.stop()


if __name__ == "__main__":

    setLogLevel("info")

    create_topology()