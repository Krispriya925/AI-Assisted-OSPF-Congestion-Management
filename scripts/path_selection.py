import csv
from pathlib import Path
from datetime import datetime, timedelta

import networkx as nx

from topology_graph import create_topology_graph


# --------------------------------------------------
# PATH HEALTH SCORE WEIGHTS
# --------------------------------------------------

WEIGHTS = {
    "delay": 0.30,
    "utilization": 0.25,
    "packet_loss": 0.25,
    "bandwidth": 0.15,
    "routing_cost": 0.05,
}

METRICS_FILE = Path(__file__).resolve().parent.parent / "data" / "link_metrics.csv"
CAPACITY_MBPS = 10.0

# These remain illustrative until real link-level measurements exist.
DEMO_METRICS = {
    ("r1", "r2"): {"delay_ms": 0.8, "packet_loss_pct": 0.2},
    ("r1", "r3"): {"delay_ms": 2.5, "packet_loss_pct": 3.0},
    ("r1", "r6"): {"delay_ms": 0.5, "packet_loss_pct": 0.1},
    ("r2", "r3"): {"delay_ms": 1.0, "packet_loss_pct": 0.5},
    ("r2", "r4"): {"delay_ms": 0.7, "packet_loss_pct": 0.2},
    ("r3", "r4"): {"delay_ms": 3.0, "packet_loss_pct": 4.0},
    ("r3", "r5"): {"delay_ms": 0.6, "packet_loss_pct": 0.1},
    ("r4", "r5"): {"delay_ms": 0.9, "packet_loss_pct": 0.3},
    ("r5", "r6"): {"delay_ms": 0.4, "packet_loss_pct": 0.1},
}


def load_latest_utilization(csv_path=METRICS_FILE):
    """Calculate average utilization over the latest 30-second data window.

    The window is relative to the newest valid timestamp in the CSV,
    so historical files can also be tested.
    The higher endpoint average is used conservatively.
    """

    if not csv_path.exists():
        raise FileNotFoundError(f"Metrics CSV not found: {csv_path}")

    samples = {}

    with csv_path.open("r", newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        required = {
            "timestamp",
            "link",
            "a_utilization_pct",
            "b_utilization_pct",
        }

        if not reader.fieldnames or not required.issubset(reader.fieldnames):
            raise ValueError(
                f"CSV is missing required columns: {required}"
            )

        for row in reader:
            link_name = row["link"].strip()
            timestamp_text = row["timestamp"].strip()

            if not link_name or not timestamp_text:
                continue

            try:
                timestamp = datetime.fromisoformat(timestamp_text)
                a_util = float(row["a_utilization_pct"])
                b_util = float(row["b_utilization_pct"])
            except (TypeError, ValueError):
                continue

            if not (0 <= a_util <= 100 and 0 <= b_util <= 100):
                continue

            samples.setdefault(link_name, []).append({
                "timestamp": timestamp,
                "timestamp_text": timestamp_text,
                "a_util": a_util,
                "b_util": b_util,
            })

    if not samples:
        raise ValueError("No valid utilization samples found in CSV.")

    newest_timestamp = max(
        sample["timestamp"]
        for link_samples in samples.values()
        for sample in link_samples
    )

    window_start = newest_timestamp - timedelta(seconds=30)
    result = {}

    for link_name, link_samples in samples.items():
        recent = [
            sample for sample in link_samples
            if window_start <= sample["timestamp"] <= newest_timestamp
        ]

        # Fall back to the latest valid sample if no recent samples exist.
        if not recent:
            recent = [
                max(link_samples, key=lambda sample: sample["timestamp"])
            ]

        average_a = sum(s["a_util"] for s in recent) / len(recent)
        average_b = sum(s["b_util"] for s in recent) / len(recent)

        result[link_name] = {
            "timestamp": max(
                recent, key=lambda sample: sample["timestamp"]
            )["timestamp_text"],
            "utilization_pct": max(average_a, average_b),
            "sample_count": len(recent),
            "window_seconds": 30,
        }

    return result


def attach_metrics(graph, latest_utilization):
    """Attach live utilization and explicitly illustrative delay/loss."""

    missing = []

    for (router_a, router_b), demo in DEMO_METRICS.items():
        link_name = f"{router_a.upper()}-{router_b.upper()}"

        # CSV names use the same router-pair names regardless of edge order.
        if link_name not in latest_utilization:
            link_name = f"{router_b.upper()}-{router_a.upper()}"

        if link_name not in latest_utilization:
            missing.append(f"{router_a}-{router_b}")
            continue

        utilization = latest_utilization[link_name]["utilization_pct"]

        graph[router_a][router_b].update({
            "delay_ms": demo["delay_ms"],
            "utilization_pct": utilization,
            "packet_loss_pct": demo["packet_loss_pct"],
            "metrics_source": "live utilization; illustrative delay/loss",
            "metrics_timestamp": latest_utilization[link_name]["timestamp"],
        })

    if missing:
        raise ValueError(
            "No valid utilization samples found for: " + ", ".join(missing)
        )

    return graph


def calculate_path_metrics(graph, path):
    """Aggregate link metrics into end-to-end path metrics."""

    links = [
        graph[path[i]][path[i + 1]]
        for i in range(len(path) - 1)
    ]

    total_delay = sum(link["delay_ms"] for link in links)

    delivery_probability = 1.0
    for link in links:
        loss_fraction = link["packet_loss_pct"] / 100.0
        delivery_probability *= 1.0 - loss_fraction

    total_packet_loss = (1.0 - delivery_probability) * 100.0

    available_bandwidth = min(
        link["bandwidth_mbps"]
        * (1.0 - link["utilization_pct"] / 100.0)
        for link in links
    )

    max_utilization = max(
        link["utilization_pct"] for link in links
    )

    total_routing_cost = sum(link["cost"] for link in links)

    return {
        "delay": total_delay,
        "utilization": max_utilization,
        "packet_loss": total_packet_loss,
        "bandwidth": available_bandwidth,
        "routing_cost": total_routing_cost,
        "hops": len(links),
    }


def normalize(values, higher_is_better):
    minimum = min(values)
    maximum = max(values)

    if maximum == minimum:
        return [1.0] * len(values)

    scores = []
    for value in values:
        score = (value - minimum) / (maximum - minimum)
        if not higher_is_better:
            score = 1.0 - score
        scores.append(score)

    return scores


def calculate_health_scores(path_results):
    metric_directions = {
        "delay": False,
        "utilization": False,
        "packet_loss": False,
        "bandwidth": True,
        "routing_cost": False,
    }

    normalized_metrics = {}

    for metric, higher_is_better in metric_directions.items():
        values = [
            result["metrics"][metric] for result in path_results
        ]
        normalized_metrics[metric] = normalize(
            values, higher_is_better
        )

    for index, result in enumerate(path_results):
        result["health_score"] = sum(
            WEIGHTS[metric] * normalized_metrics[metric][index]
            for metric in WEIGHTS
        ) * 100.0

    return path_results


def select_best_path(source="r1", destination="r5", k=8):
    graph = create_topology_graph()
    latest_utilization = load_latest_utilization()
    attach_metrics(graph, latest_utilization)

    candidates = nx.shortest_simple_paths(
        graph, source, destination, weight="cost"
    )

    path_results = []

    for path in candidates:
        if len(path_results) >= k:
            break

        path_results.append({
            "path": path,
            "metrics": calculate_path_metrics(graph, path),
        })

    if not path_results:
        print("No candidate paths found.")
        return None

    calculate_health_scores(path_results)
    path_results.sort(
        key=lambda result: result["health_score"],
        reverse=True,
    )

    print("\n" + "=" * 72)
    print("AI-ASSISTED PATH HEALTH ANALYSIS")
    print("=" * 72)
    print("Utilization: latest measurements from link_metrics.csv")
    print("Delay/loss: illustrative values, not live measurements.")
    print("Scores are relative to the candidate paths in this run.\n")

    for rank, result in enumerate(path_results, start=1):
        metrics = result["metrics"]
        print(f"Rank {rank}: {' -> '.join(result['path'])}")
        print(f"  Path Health Score : {result['health_score']:.2f}/100")
        print(f"  Total Delay       : {metrics['delay']:.2f} ms (illustrative)")
        print(f"  Max Link Usage    : {metrics['utilization']:.4f}% (measured)")
        print(f"  End-to-End Loss   : {metrics['packet_loss']:.3f}% (illustrative)")
        print(f"  Available BW      : {metrics['bandwidth']:.4f} Mbps (estimated)")
        print(f"  Total OSPF Cost   : {metrics['routing_cost']}")
        print(f"  Hops              : {metrics['hops']}")
        print()

    best = path_results[0]
    print("-" * 72)
    print("RECOMMENDED PATH:", " -> ".join(best["path"]))
    print(f"HEALTH SCORE: {best['health_score']:.2f}/100")
    print("-" * 72)

    return best


if __name__ == "__main__":
    select_best_path()
