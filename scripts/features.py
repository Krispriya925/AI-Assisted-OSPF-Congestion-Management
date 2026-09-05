import pandas as pd

INPUT = "data/processed_data.csv"
OUTPUT = "data/features.csv"

df = pd.read_csv(INPUT)

df["timestamp"] = pd.to_datetime(df["timestamp"])

# Time between two measurements
df["time_diff"] = df["timestamp"].diff().dt.total_seconds()

# Difference in cumulative counters
df["rx_bytes_diff"] = df["rx_bytes"].diff()
df["tx_bytes_diff"] = df["tx_bytes"].diff()

df["rx_packets_diff"] = df["rx_packets"].diff()
df["tx_packets_diff"] = df["tx_packets"].diff()

# Convert bytes/sec to Mbits/sec
df["rx_rate"] = (
    df["rx_bytes_diff"] * 8
    / df["time_diff"]
    / 1_000_000
)

df["tx_rate"] = (
    df["tx_bytes_diff"] * 8
    / df["time_diff"]
    / 1_000_000
)

# Packets per second
df["packet_rate"] = (
    df["tx_packets_diff"]
    / df["time_diff"]
)

# Main latency feature
df["latency"] = df["avg_latency"]

# First row has no previous measurement
df = df.dropna()

features = df[
    [
        "timestamp",
        "rx_rate",
        "tx_rate",
        "packet_rate",
        "min_latency",
        "avg_latency",
        "max_latency",
        "latency"
    ]
]

features.to_csv(OUTPUT, index=False)

print("\nFeature dataset:")
print(features)

print("\nShape:", features.shape)

print(f"\n[OK] Features saved to {OUTPUT}")
