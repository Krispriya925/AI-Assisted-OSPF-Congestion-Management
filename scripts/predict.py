import pandas as pd
import joblib

MODEL = "models/congestion_model.pkl"
INPUT = "data/labeled_data.csv"

# Load trained model
model = joblib.load(MODEL)

# Load latest network data
df = pd.read_csv(INPUT)

# Features used during training
FEATURES = [
    "rx_rate",
    "tx_rate",
    "packet_rate",
    "min_latency",
    "max_latency"
]

# Take the latest measurement
latest = df.iloc[-1]

X = pd.DataFrame([latest[FEATURES].values], columns=FEATURES)

# Prediction
prediction = model.predict(X)[0]

# Prediction probability
probability = model.predict_proba(X)[0]

print("\n===================================")
print("AI-OSPF Congestion Prediction")
print("===================================")

print(f"RX Rate       : {latest['rx_rate']:.6f} Mbit/s")
print(f"TX Rate       : {latest['tx_rate']:.6f} Mbit/s")
print(f"Packet Rate   : {latest['packet_rate']:.2f} packets/s")
print(f"Min Latency   : {latest['min_latency']:.3f} ms")
print(f"Max Latency   : {latest['max_latency']:.3f} ms")

if prediction == 1:
    status = "CONGESTED"
else:
    status = "NORMAL"

confidence = probability[prediction] * 100

print("-----------------------------------")
print(f"Prediction    : {status}")
print(f"Confidence    : {confidence:.2f}%")
print("===================================")
