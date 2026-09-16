import pandas as pd

INPUT = "data/features.csv"
OUTPUT = "data/labeled_data.csv"

# Load feature dataset
df = pd.read_csv(INPUT)

# --------------------------------------------------
# Warning thresholds
# --------------------------------------------------
UTILIZATION_WARNING = 80      # %
DELAY_WARNING = 1.0           # ms
PACKET_LOSS_WARNING = 2.0     # %

# --------------------------------------------------
# Critical thresholds
# --------------------------------------------------
UTILIZATION_CRITICAL = 95     # %
DELAY_CRITICAL = 5.0          # ms
PACKET_LOSS_CRITICAL = 5.0    # %

# --------------------------------------------------
# Calculate warning indicators
# --------------------------------------------------

df["utilization_warning"] = (
    df["utilization"] > UTILIZATION_WARNING
).astype(int)

df["delay_warning"] = (
    df["avg_latency"] > DELAY_WARNING
).astype(int)

df["packet_loss_warning"] = (
    df["packet_loss"] > PACKET_LOSS_WARNING
).astype(int)

# Count how many warning conditions are active
df["congestion_score"] = (
    df["utilization_warning"]
    + df["delay_warning"]
    + df["packet_loss_warning"]
)

# --------------------------------------------------
# Calculate critical condition
# --------------------------------------------------

df["critical_condition"] = (
    (df["utilization"] > UTILIZATION_CRITICAL)
    | (df["avg_latency"] > DELAY_CRITICAL)
    | (df["packet_loss"] > PACKET_LOSS_CRITICAL)
).astype(int)

# --------------------------------------------------
# Final congestion label
#
# 0 = Normal
# 1 = Congested
# 2 = Critical
# --------------------------------------------------

df["congestion"] = 0

# Critical condition has highest priority
df.loc[
    df["critical_condition"] == 1,
    "congestion"
] = 2

# If no critical condition,
# 2 or more warning conditions = Congested
df.loc[
    (df["critical_condition"] == 0)
    & (df["congestion_score"] >= 2),
    "congestion"
] = 1

# --------------------------------------------------
# Display results
# --------------------------------------------------

print("\nCongestion label distribution:")
print(df["congestion"].value_counts().sort_index())

print("\nLabel meaning:")
print("0 = NORMAL")
print("1 = CONGESTED")
print("2 = CRITICAL")

print("\nLabeled dataset:")
print(df.head(20))

# Save labeled dataset
df.to_csv(OUTPUT, index=False)

print(f"\n[OK] Labeled dataset saved to {OUTPUT}")