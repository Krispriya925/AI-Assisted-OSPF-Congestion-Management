
import csv
import os
import re
import subprocess
import time
from datetime import datetime

# All nine router-to-router links.
# Each entry: link name, endpoint A, interface A, endpoint B, interface B.
LINKS = [
    ("R1-R2", "r1", "r1-eth1", "r2", "r2-eth0"),
    ("R1-R3", "r1", "r1-eth2", "r3", "r3-eth0"),
    ("R1-R6", "r1", "r1-eth3", "r6", "r6-eth0"),
    ("R2-R3", "r2", "r2-eth1", "r3", "r3-eth1"),
    ("R2-R4", "r2", "r2-eth2", "r4", "r4-eth0"),
    ("R3-R4", "r3", "r3-eth2", "r4", "r4-eth1"),
    ("R3-R5", "r3", "r3-eth3", "r5", "r5-eth0"),
    ("R4-R5", "r4", "r4-eth2", "r5", "r5-eth1"),
    ("R5-R6", "r5", "r5-eth2", "r6", "r6-eth1"),
]

CAPACITY_MBPS = 10.0
SAMPLE_INTERVAL = 2.0
OUTPUT_FILE = "data/link_metrics.csv"


def get_namespace_pid(node):
    """Find the Mininet node's namespace shell PID."""
    result = subprocess.run(
        ["sudo", "pgrep", "-f",
         rf"^bash --norc --noediting -is mininet:{node}$"],
        capture_output=True,
        text=True,
        check=False,
    )

    pids = result.stdout.strip().splitlines()
    if not pids:
        raise RuntimeError(
            f"Cannot find {node}. Is the Mininet topology running?"
        )

    return int(pids[0])


def get_interface_counters(node, interface):
    """Read RX/TX bytes and packet counts from one interface."""
    pid = get_namespace_pid(node)

    result = subprocess.run(
        ["sudo", "mnexec", "-a", str(pid),
         "ip", "-s", "link", "show", interface],
        capture_output=True,
        text=True,
        check=True,
    )

    rx_match = re.search(
        r"RX:\s+bytes\s+packets.*?\n\s*(\d+)\s+(\d+)",
        result.stdout,
        re.S,
    )
    tx_match = re.search(
        r"TX:\s+bytes\s+packets.*?\n\s*(\d+)\s+(\d+)",
        result.stdout,
        re.S,
    )

    if not rx_match or not tx_match:
        raise RuntimeError(
            f"Could not parse counters for {node}:{interface}"
        )

    return {
        "rx_bytes": int(rx_match.group(1)),
        "rx_packets": int(rx_match.group(2)),
        "tx_bytes": int(tx_match.group(1)),
        "tx_packets": int(tx_match.group(2)),
    }


def collect_snapshot():
    """Read counters for both endpoints of all nine links."""
    snapshot = {}

    for link, node_a, iface_a, node_b, iface_b in LINKS:
        snapshot[(link, "A")] = (
            node_a, iface_a, get_interface_counters(node_a, iface_a)
        )
        snapshot[(link, "B")] = (
            node_b, iface_b, get_interface_counters(node_b, iface_b)
        )

    return snapshot


def main():
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    file_exists = os.path.exists(OUTPUT_FILE)

    fields = [
        "timestamp", "link",
        "node_a", "interface_a", "node_b", "interface_b",
        "a_rx_mbps", "a_tx_mbps",
        "b_rx_mbps", "b_tx_mbps",
        "a_utilization_pct", "b_utilization_pct",
        "a_rx_packets_per_sec", "a_tx_packets_per_sec",
        "b_rx_packets_per_sec", "b_tx_packets_per_sec",
    ]

    print("Collecting real router-link metrics.")
    print(f"Links: {len(LINKS)} | Sample interval: {SAMPLE_INTERVAL}s")
    print(f"Output: {OUTPUT_FILE}")
    print("Press Ctrl+C to stop.\n")

    previous = collect_snapshot()
    previous_time = time.monotonic()

    try:
        while True:
            time.sleep(SAMPLE_INTERVAL)

            current = collect_snapshot()
            current_time = time.monotonic()
            elapsed = current_time - previous_time
            timestamp = datetime.now().astimezone().isoformat()

            with open(OUTPUT_FILE, "a", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=fields)

                if not file_exists:
                    writer.writeheader()
                    file_exists = True

                for link, node_a, iface_a, node_b, iface_b in LINKS:
                    a = current[(link, "A")][2]
                    pa = previous[(link, "A")][2]
                    b = current[(link, "B")][2]
                    pb = previous[(link, "B")][2]

                    # Counter resets can happen if an interface is recreated.
                    def delta(now, before):
                        return max(0, now - before)

                    def rate_mbps(byte_delta):
                        return byte_delta * 8 / elapsed / 1_000_000

                    a_rx = rate_mbps(delta(a["rx_bytes"], pa["rx_bytes"]))
                    a_tx = rate_mbps(delta(a["tx_bytes"], pa["tx_bytes"]))
                    b_rx = rate_mbps(delta(b["rx_bytes"], pb["rx_bytes"]))
                    b_tx = rate_mbps(delta(b["tx_bytes"], pb["tx_bytes"]))

                    row = {
                        "timestamp": timestamp,
                        "link": link,
                        "node_a": node_a,
                        "interface_a": iface_a,
                        "node_b": node_b,
                        "interface_b": iface_b,
                        "a_rx_mbps": round(a_rx, 6),
                        "a_tx_mbps": round(a_tx, 6),
                        "b_rx_mbps": round(b_rx, 6),
                        "b_tx_mbps": round(b_tx, 6),
                        "a_utilization_pct": round(
                            max(a_rx, a_tx) / CAPACITY_MBPS * 100, 4
                        ),
                        "b_utilization_pct": round(
                            max(b_rx, b_tx) / CAPACITY_MBPS * 100, 4
                        ),
                        "a_rx_packets_per_sec": round(
                            delta(a["rx_packets"], pa["rx_packets"]) / elapsed, 3
                        ),
                        "a_tx_packets_per_sec": round(
                            delta(a["tx_packets"], pa["tx_packets"]) / elapsed, 3
                        ),
                        "b_rx_packets_per_sec": round(
                            delta(b["rx_packets"], pb["rx_packets"]) / elapsed, 3
                        ),
                        "b_tx_packets_per_sec": round(
                            delta(b["tx_packets"], pb["tx_packets"]) / elapsed, 3
                        ),
                    }

                    writer.writerow(row)
                    print(
                        f"{link}: A utilization={row['a_utilization_pct']:.4f}% "
                        f"| B utilization={row['b_utilization_pct']:.4f}%"
                    )

            previous = current
            previous_time = current_time

    except KeyboardInterrupt:
        print(f"\nCollector stopped. Data saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
