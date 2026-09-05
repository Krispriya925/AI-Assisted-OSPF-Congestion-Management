import subprocess
import re
import time
import csv
import os
from datetime import datetime


def get_namespace_pid(node):
    """Find the Mininet namespace process for a node."""
    result = subprocess.run(
        ["pgrep", "-f", f"mininet:{node}"],
        capture_output=True,
        text=True
    )

    pids = result.stdout.strip().splitlines()

    if not pids:
        return None

    return pids[0]


def run_in_node(node, command):
    """Run a command inside a Mininet node."""

    pid = get_namespace_pid(node)

    if not pid:
        print(f"[ERROR] Could not find Mininet node: {node}")
        return ""

    result = subprocess.run(
        ["sudo", "mnexec", "-a", pid, "bash", "-c", command],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"[ERROR] {node}: {result.stderr.strip()}")

    return result.stdout


def get_interface_stats(node, interface):

    output = run_in_node(
        node,
        f"ip -s link show {interface}"
    )

    rx = re.search(
        r"RX:\s+bytes packets.*\n\s*(\d+)\s+(\d+)",
        output
    )

    tx = re.search(
        r"TX:\s+bytes packets.*\n\s*(\d+)\s+(\d+)",
        output
    )

    if rx and tx:
        return {
            "rx_bytes": int(rx.group(1)),
            "rx_packets": int(rx.group(2)),
            "tx_bytes": int(tx.group(1)),
            "tx_packets": int(tx.group(2))
        }

    print("[ERROR] Could not parse interface statistics")
    return None


def get_ping():

    output = run_in_node(
        "h1",
        "ping -c 5 -W 1 10.0.3.1"
    )

    match = re.search(
        r"rtt min/avg/max/mdev = "
        r"([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)",
        output
    )

    if match:
        return {
            "min_latency": float(match.group(1)),
            "avg_latency": float(match.group(2)),
            "max_latency": float(match.group(3))
        }

    print("[ERROR] Could not parse ping latency")
    return None


def collect_data():

    print("\nCollecting network data...")

    stats = get_interface_stats(
        "r1",
        "r1-eth1"
    )

    ping = get_ping()

    if stats and ping:

        row = {
            "timestamp": datetime.now().isoformat(),
            **stats,
            **ping
        }

        print(row)

        os.makedirs("data", exist_ok=True)

        file_path = "data/network_data.csv"

        file_exists = os.path.exists(file_path)

        with open(
            file_path,
            "a",
            newline=""
        ) as f:

            fieldnames = [
                "timestamp",
                "rx_bytes",
                "rx_packets",
                "tx_bytes",
                "tx_packets",
                "min_latency",
                "avg_latency",
                "max_latency"
            ]

            writer = csv.DictWriter(
                f,
                fieldnames=fieldnames
            )

            if not file_exists or os.path.getsize(file_path) == 0:
                writer.writeheader()

            writer.writerow(row)

        print("[OK] Data saved to data/network_data.csv")

    else:

        print("[WARNING] Data collection failed")


if __name__ == "__main__":

    print("=" * 50)
    print("AI-OSPF Network Monitor")
    print("=" * 50)
    print("Monitoring r1-eth1 and h1 -> h2 latency")
    print("Press Ctrl+C to stop")
    print("=" * 50)

    try:

        while True:

            collect_data()

            time.sleep(5)

    except KeyboardInterrupt:

        print("\nMonitoring stopped.")
