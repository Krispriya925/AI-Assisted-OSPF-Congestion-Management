import subprocess
import re
import time
import csv
import os
from datetime import datetime


# ==================================================
# CONFIGURATION
# ==================================================

MONITOR_NODE = "r1"
MONITOR_INTERFACE = "r1-eth2"

PING_NODE = "h1"
PING_DESTINATION = "10.0.5.1"

LINK_CAPACITY_MBPS = 10

PING_COUNT = 50
PING_INTERVAL = 0.05
PING_TIMEOUT = 1


# ==================================================
# FIND MININET NODE
# ==================================================

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


# ==================================================
# RUN COMMAND INSIDE MININET NODE
# ==================================================

def run_in_node(node, command):
    """Run a command inside a Mininet node."""

    pid = get_namespace_pid(node)

    if not pid:
        print(f"[ERROR] Could not find Mininet node: {node}")
        return ""

    result = subprocess.run(
        [
            "sudo",
            "mnexec",
            "-a",
            pid,
            "bash",
            "-c",
            command
        ],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(
            f"[ERROR] {node}: "
            f"{result.stderr.strip()}"
        )

    return result.stdout


# ==================================================
# GET INTERFACE STATISTICS
# ==================================================

def get_interface_stats(node, interface):

    output = run_in_node(
        node,
        f"ip -s link show {interface}"
    )

    rx = re.search(
        r"RX:\s+bytes\s+packets\s+errors\s+dropped.*?\n"
        r"\s*(\d+)\s+(\d+)",
        output,
        re.DOTALL
    )

    tx = re.search(
        r"TX:\s+bytes\s+packets\s+errors\s+dropped.*?\n"
        r"\s*(\d+)\s+(\d+)",
        output,
        re.DOTALL
    )

    if rx and tx:

        return {
            "rx_bytes": int(rx.group(1)),
            "rx_packets": int(rx.group(2)),
            "tx_bytes": int(tx.group(1)),
            "tx_packets": int(tx.group(2))
        }

    print(
        "[ERROR] Could not parse "
        "interface statistics"
    )

    return None


# ==================================================
# CALCULATE UTILIZATION
# ==================================================

def calculate_utilization(previous, current, elapsed):

    if previous is None:
        return None

    rx_bytes_diff = (
        current["rx_bytes"]
        - previous["rx_bytes"]
    )

    tx_bytes_diff = (
        current["tx_bytes"]
        - previous["tx_bytes"]
    )

    # Convert bytes/sec to Mbps
    rx_rate = (
        rx_bytes_diff * 8
        / elapsed
        / 1_000_000
    )

    tx_rate = (
        tx_bytes_diff * 8
        / elapsed
        / 1_000_000
    )

    # Full-duplex link:
    # use the busier direction
    max_rate = max(rx_rate, tx_rate)

    utilization = (
        max_rate
        / LINK_CAPACITY_MBPS
        * 100
    )

    return {
        "rx_rate": rx_rate,
        "tx_rate": tx_rate,
        "utilization": utilization
    }


# ==================================================
# GET PING INFORMATION
# ==================================================

def get_ping():

    command = (
        f"ping "
        f"-c {PING_COUNT} "
        f"-i {PING_INTERVAL} "
        f"-W {PING_TIMEOUT} "
        f"{PING_DESTINATION}"
    )

    output = run_in_node(
        PING_NODE,
        command
    )

    # ----------------------------------------------
    # Packet loss
    # ----------------------------------------------

    loss_match = re.search(
        r"(\d+(?:\.\d+)?)%\s+packet loss",
        output
    )

    # ----------------------------------------------
    # RTT
    # ----------------------------------------------

    rtt_match = re.search(
        r"rtt min/avg/max/mdev = "
        r"([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)",
        output
    )

    if not loss_match:
        print(
            "[ERROR] Could not parse "
            "packet loss"
        )
        return None

    packet_loss = float(
        loss_match.group(1)
    )

    result = {
        "packet_loss": packet_loss
    }

    if rtt_match:

        result.update({
            "min_latency":
                float(rtt_match.group(1)),

            "avg_latency":
                float(rtt_match.group(2)),

            "max_latency":
                float(rtt_match.group(3))
        })

    else:

        result.update({
            "min_latency": None,
            "avg_latency": None,
            "max_latency": None
        })

    return result


# ==================================================
# COLLECT DATA
# ==================================================

def collect_data(previous_stats, previous_time):

    print("\nCollecting network data...")

    current_stats = get_interface_stats(
        MONITOR_NODE,
        MONITOR_INTERFACE
    )

    current_time = time.time()

    if not current_stats:

        print(
            "[WARNING] Interface "
            "statistics unavailable"
        )

        return previous_stats, current_time

    ping = get_ping()

    if not ping:

        print(
            "[WARNING] Ping measurement failed"
        )

        return current_stats, current_time

    # ----------------------------------------------
    # Calculate elapsed time
    # ----------------------------------------------

    elapsed = None

    utilization_data = None

    if previous_stats is not None:

        elapsed = (
            current_time
            - previous_time
        )

        utilization_data = calculate_utilization(
            previous_stats,
            current_stats,
            elapsed
        )

    # ----------------------------------------------
    # First measurement
    # ----------------------------------------------

    if utilization_data is None:

        print(
            "[INFO] First measurement. "
            "Waiting for next sample "
            "to calculate utilization."
        )

        return current_stats, current_time

    # ----------------------------------------------
    # Create row
    # ----------------------------------------------

    row = {
        "timestamp":
            datetime.now().isoformat(),

        "rx_bytes":
            current_stats["rx_bytes"],

        "rx_packets":
            current_stats["rx_packets"],

        "tx_bytes":
            current_stats["tx_bytes"],

        "tx_packets":
            current_stats["tx_packets"],

        "rx_rate":
            utilization_data["rx_rate"],

        "tx_rate":
            utilization_data["tx_rate"],

        "utilization":
            utilization_data["utilization"],

        "min_latency":
            ping["min_latency"],

        "avg_latency":
            ping["avg_latency"],

        "max_latency":
            ping["max_latency"],

        "packet_loss":
            ping["packet_loss"]
    }

    # ----------------------------------------------
    # Display
    # ----------------------------------------------

    print(
        f"Utilization : "
        f"{row['utilization']:.2f}%"
    )

    print(
        f"RX Rate     : "
        f"{row['rx_rate']:.4f} Mbps"
    )

    print(
        f"TX Rate     : "
        f"{row['tx_rate']:.4f} Mbps"
    )

    avg_latency_display = (
    f"{row['avg_latency']:.3f} ms"
    if row["avg_latency"] is not None
    else "N/A"
    )

    print(
    f"Avg Delay   : "
    f"{avg_latency_display}"
    )

    print(
        f"Packet Loss : "
        f"{row['packet_loss']:.2f}%"
    )

    # ----------------------------------------------
    # Save CSV
    # ----------------------------------------------

    os.makedirs(
        "data",
        exist_ok=True
    )

    file_path = "data/network_data.csv"

    fieldnames = [
        "timestamp",
        "rx_bytes",
        "rx_packets",
        "tx_bytes",
        "tx_packets",
        "rx_rate",
        "tx_rate",
        "utilization",
        "min_latency",
        "avg_latency",
        "max_latency",
        "packet_loss"
    ]

    file_exists = os.path.exists(
        file_path
    )

    with open(
        file_path,
        "a",
        newline=""
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        if (
            not file_exists
            or os.path.getsize(file_path) == 0
        ):
            writer.writeheader()

        writer.writerow(row)

    print(
        "[OK] Data saved to "
        "data/network_data.csv"
    )

    return current_stats, current_time


# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":

    print("=" * 50)
    print("AI-OSPF Network Monitor")
    print("=" * 50)

    print(
        f"Monitoring : "
        f"{MONITOR_NODE}/{MONITOR_INTERFACE}"
    )

    print(
        f"Link Capacity : "
        f"{LINK_CAPACITY_MBPS} Mbps"
    )

    print(
        f"Ping : "
        f"{PING_NODE} -> "
        f"{PING_DESTINATION}"
    )

    print(
        "Metrics: Utilization | "
        "Delay | Packet Loss"
    )

    print("Press Ctrl+C to stop")
    print("=" * 50)

    previous_stats = None
    previous_time = None

    try:

        while True:

            previous_stats, previous_time = collect_data(
                previous_stats,
                previous_time
            )

            time.sleep(5)

    except KeyboardInterrupt:

        print(
            "\nMonitoring stopped."
        )