
import networkx as nx


def create_topology_graph():
    """
    Logical representation of the current six-router Mininet topology.
    Router-to-router links use the configured 10 Mbps bandwidth.
    """

    G = nx.Graph()

    # Routers
    routers = ["r1", "r2", "r3", "r4", "r5", "r6"]
    G.add_nodes_from(routers)

    # Router-to-router links:
    # (router 1, router 2, subnet, OSPF cost, bandwidth Mbps)
    links = [
        ("r1", "r2", "10.0.12.0/24", 10, 10),
        ("r1", "r3", "10.0.13.0/24", 10, 10),
        ("r1", "r6", "10.0.16.0/24", 10, 10),
        ("r2", "r3", "10.0.23.0/24", 10, 10),
        ("r2", "r4", "10.0.24.0/24", 10, 10),
        ("r3", "r4", "10.0.34.0/24", 10, 10),
        ("r3", "r5", "10.0.35.0/24", 10, 10),
        ("r4", "r5", "10.0.45.0/24", 10, 10),
        ("r5", "r6", "10.0.56.0/24", 10, 10),
    ]

    for source, destination, subnet, cost, bandwidth in links:
        G.add_edge(
            source,
            destination,
            network=subnet,
            cost=cost,
            bandwidth_mbps=bandwidth
        )

    return G


def display_topology(G):
    print("\n==============================")
    print("SIX-ROUTER NETWORK TOPOLOGY")
    print("==============================")

    print("\nRouters:")
    print(", ".join(sorted(G.nodes())))

    print("\nRouter-to-router links:")

    for source, destination, data in sorted(
        G.edges(data=True)
    ):
        print(
            f"{source} <--> {destination}"
            f" | Network: {data['network']}"
            f" | Cost: {data['cost']}"
            f" | Bandwidth: {data['bandwidth_mbps']} Mbps"
        )


if __name__ == "__main__":
    topology = create_topology_graph()
    display_topology(topology)

    print("\n==============================")
    print("CANDIDATE PATHS: R1 TO R5")
    print("==============================")

    paths = nx.all_simple_paths(
        topology,
        source="r1",
        target="r5"
    )

    for index, path in enumerate(paths, start=1):
        print(f"{index}. {' -> '.join(path)}")
