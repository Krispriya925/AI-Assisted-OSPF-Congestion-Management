import networkx as nx

from predict import predict_congestion


CONGESTION_PENALTY = 100


def build_topology():

    G = nx.Graph()

    G.add_edge("r1", "r2", cost=10, congested=False)
    G.add_edge("r1", "r3", cost=10, congested=False)
    G.add_edge("r2", "r3", cost=10, congested=False)

    return G


def calculate_path_cost(G, path):

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


def apply_ai_prediction(G):

    prediction, status, confidence, latest = predict_congestion()

    print("\n==============================")
    print("AI CONGESTION DECISION")
    print("==============================")

    print(f"Prediction : {status}")
    print(f"Confidence : {confidence:.2f}%")

    if prediction == 1:

        print("Congestion detected!")
        print("Applying penalty to R1-R3 link.")

        G["r1"]["r3"]["congested"] = True

    else:

        print("Network is normal.")
        print("No congestion penalty applied.")

    return G


if __name__ == "__main__":

    source = "r1"
    destination = "r3"

    # Build topology
    G = build_topology()

    # ----------------------------------------
    # AI prediction
    # ----------------------------------------

    G = apply_ai_prediction(G)

    # ----------------------------------------
    # Select best path
    # ----------------------------------------

    select_best_path(
        G,
        source,
        destination
    )