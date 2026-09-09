import networkx as nx


CONGESTION_PENALTY = 100


def build_topology():
    """
    Build the current 3-router topology.
    """

    G = nx.Graph()

    G.add_edge("r1", "r2", cost=10, congested=False)
    G.add_edge("r1", "r3", cost=10, congested=False)
    G.add_edge("r2", "r3", cost=10, congested=False)

    return G


def calculate_path_cost(G, path):
    """
    Calculate total cost of a path.

    Normal link:
        cost = OSPF cost

    Congested link:
        cost = OSPF cost + congestion penalty
    """

    total_cost = 0

    for i in range(len(path) - 1):

        source = path[i]
        destination = path[i + 1]

        link = G[source][destination]

        cost = link["cost"]

        if link["congested"]:
            cost += CONGESTION_PENALTY

        total_cost += cost

    return total_cost


def get_k_shortest_paths(G, source, destination, k=3):

    paths = nx.shortest_simple_paths(
        G,
        source,
        destination,
        weight="cost"
    )

    selected_paths = []

    for i, path in enumerate(paths):

        if i >= k:
            break

        cost = calculate_path_cost(G, path)

        selected_paths.append((path, cost))

    return selected_paths


def select_best_path(G, source, destination, k=3):

    paths = get_k_shortest_paths(
        G,
        source,
        destination,
        k
    )

    print("\n==============================")
    print("AI-AWARE PATH SELECTION")
    print("==============================")

    for i, (path, cost) in enumerate(paths):

        print(
            f"Path {i + 1}: "
            f"{' -> '.join(path)}"
        )

        print(f"Final Cost: {cost}")
        print()

    best_path, best_cost = min(
        paths,
        key=lambda x: x[1]
    )

    print("------------------------------")
    print(
        f"SELECTED PATH: "
        f"{' -> '.join(best_path)}"
    )
    print(f"SELECTED COST: {best_cost}")
    print("------------------------------")

    return best_path, best_cost


if __name__ == "__main__":

    G = build_topology()

    source = "r1"
    destination = "r3"

    # --------------------------------------------------
    # TEST 1: Normal network
    # --------------------------------------------------

    print("\n\nTEST 1: NORMAL NETWORK")

    select_best_path(
        G,
        source,
        destination
    )

    # --------------------------------------------------
    # TEST 2: R1-R3 is congested
    # --------------------------------------------------

    print("\n\nTEST 2: R1-R3 CONGESTED")

    G["r1"]["r3"]["congested"] = True

    select_best_path(
        G,
        source,
        destination
    )