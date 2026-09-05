import pandas as pd

INPUT = "data/features.csv"
OUTPUT = "data/labeled_data.csv"

# Load feature dataset
df = pd.read_csv(INPUT)

# Create congestion label
# 0 = Normal
# 1 = Congested
#
# If average latency is greater than 1 ms,
# classify the sample as congested.

df["congestion"] = (
    df["avg_latency"] > 1.0
).astype(int)

print("\nCongestion label distribution:")
print(df["congestion"].value_counts())

print("\nLabeled dataset:")
print(df.head(20))

# Save labeled dataset
df.to_csv(OUTPUT, index=False)

print(f"\n[OK] Labeled dataset saved to {OUTPUT}")
