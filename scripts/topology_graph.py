import networkx as nx

def create_topology_graph():
    """
    Create the logical topology of our Mininet + FRR network.
    """

    G = nx.Graph()

    # Routers
    G.add_node("r1")
    G.add_node("r2")
    G.add_node("r3")

    # Router-to-router links
    G.add_edge(
        "r1",
        "r2",
        network="10.0.12.0/24",
        cost=10
    )

    G.add_edge(
        "r1",
        "r3",
        network="10.0.13.0/24",
        cost=10
    )

    G.add_edge(
        "r2",
        "r3",
        network="10.0.23.0/24",
        cost=10
    )

    return G


def display_topology(G):

    print("\n==============================")
    print("NETWORK TOPOLOGY")
    print("==============================")

    print("\nRouters:")

    for router in G.nodes:
        print(f"  {router}")

    print("\nLinks:")

    for r1, r2, data in G.edges(data=True):

        print(
            f"  {r1} <----> {r2} "
            f"| Network: {data['network']} "
            f"| Cost: {data['cost']}"
        )


if __name__ == "__main__":

    topology = create_topology_graph()

    display_topology(topology)

    print("\n==============================")
    print("PATHS")
    print("==============================")

    paths = list(
        nx.all_simple_paths(
            topology,
            source="r1",
            target="r3"
        )
    )

    for path in paths:
        print(" -> ".join(path))