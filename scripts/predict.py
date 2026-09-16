import pandas as pd
import joblib

MODEL = "models/congestion_model.pkl"
INPUT = "data/labeled_data.csv"

FEATURES = [
    "rx_rate",
    "tx_rate",
    "packet_rate",
    "utilization",
    "min_latency",
    "avg_latency",
    "max_latency",
    "packet_loss"
]


def predict_congestion():

    # Load trained model
    model = joblib.load(MODEL)

    # Load latest network data
    df = pd.read_csv(INPUT)

    # Take latest measurement
    latest = df.iloc[-1]

    X = pd.DataFrame(
        [latest[FEATURES].values],
        columns=FEATURES
    )

    # Prediction
    prediction = model.predict(X)[0]

    # Probability
    probability = model.predict_proba(X)[0]

    confidence = probability[prediction] * 100

    if prediction == 0:
        status = "NORMAL"
    elif prediction == 1:
        status = "CONGESTED"
    elif prediction == 2:
        status = "CRITICAL"

    return prediction, status, confidence, latest


def main():

    prediction, status, confidence, latest = predict_congestion()

    print("\n===================================")
    print("AI-OSPF Congestion Prediction")
    print("===================================")

    print(f"RX Rate       : {latest['rx_rate']:.6f} Mbit/s")
    print(f"TX Rate       : {latest['tx_rate']:.6f} Mbit/s")
    print(f"Packet Rate   : {latest['packet_rate']:.2f} packets/s")
    print(f"Min Latency   : {latest['min_latency']:.3f} ms")
    print(f"Max Latency   : {latest['max_latency']:.3f} ms")
    print(f"Utilization   : {latest['utilization']:.2f}%")
    print(f"Avg Latency   : {latest['avg_latency']:.3f} ms")
    print(f"Packet Loss   : {latest['packet_loss']:.2f}%")
    print("-----------------------------------")
    print(f"Prediction    : {status}")
    print(f"Confidence    : {confidence:.2f}%")
    print("===================================")


if __name__ == "__main__":
    main()
