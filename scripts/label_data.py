
import pandas as pd

INPUT = "data/features.csv"
OUTPUT = "data/labeled_data.csv"

# Warning thresholds
UTILIZATION_WARNING = 80       # %
DELAY_WARNING = 1.0            # ms
PACKET_LOSS_WARNING = 2.0      # %

# Critical thresholds
UTILIZATION_CRITICAL = 95      # %
DELAY_CRITICAL = 5.0           # ms
PACKET_LOSS_CRITICAL = 5.0     # %

df = pd.read_csv(INPUT)

# Warning conditions
df["utilization_warning"] = (
    df["utilization"] > UTILIZATION_WARNING
).astype(int)

df["delay_warning"] = (
    df["avg_latency"] > DELAY_WARNING
).astype(int)

df["packet_loss_warning"] = (
    df["packet_loss"] > PACKET_LOSS_WARNING
).astype(int)

df["congestion_score"] = (
    df["utilization_warning"]
    + df["delay_warning"]
    + df["packet_loss_warning"]
)

# Critical condition: any one critical threshold is exceeded
df["critical_condition"] = (
    (df["utilization"] > UTILIZATION_CRITICAL)
    | (df["avg_latency"] > DELAY_CRITICAL)
    | (df["packet_loss"] > PACKET_LOSS_CRITICAL)
).astype(int)

# Assign labels
df["congestion"] = 0  # NORMAL

# One or more warnings, but no critical condition
df.loc[
    (df["congestion_score"] >= 1)
    & (df["critical_condition"] == 0),
    "congestion"
] = 1  # CONGESTED

# Critical condition takes priority
df.loc[
    df["critical_condition"] == 1,
    "congestion"
] = 2  # CRITICAL

print("\nCongestion label distribution:")
print(df["congestion"].value_counts().sort_index())

print("\nLabel meaning:")
print("0 = NORMAL")
print("1 = CONGESTED")
print("2 = CRITICAL")

print("\nSample labeled data:")
print(df.head(10).to_string(index=False))

df.to_csv(OUTPUT, index=False)

print(f"\n[OK] Labeled dataset saved to {OUTPUT}")
