import pandas as pd

INPUT = "data/network_data.csv"
OUTPUT = "data/processed_data.csv"

# Load dataset
df = pd.read_csv(INPUT)

print("Original dataset:")
print(df.head())
print("\nShape:", df.shape)

# Convert timestamp
df["timestamp"] = pd.to_datetime(df["timestamp"])

# Remove duplicate rows
df = df.drop_duplicates()

# Remove rows containing missing values
df = df.dropna()

# Sort chronologically
df = df.sort_values("timestamp")

# Save processed dataset
df.to_csv(OUTPUT, index=False)

print("\nProcessed dataset:")
print(df.head())
print("\nShape:", df.shape)

print(f"\n[OK] Saved to {OUTPUT}")
