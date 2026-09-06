import joblib
import pandas as pd


MODEL_PATH = "models/congestion_model.pkl"


# Features expected by the Random Forest model
FEATURES = [
    "rx_rate",
    "tx_rate",
    "packet_rate",
    "min_latency",
    "max_latency"
]


def load_model():
    """Load the trained congestion prediction model."""
    return joblib.load(MODEL_PATH)


def predict_congestion(model, data):
    """Predict whether the network is congested."""
    X = pd.DataFrame([data], columns=FEATURES)

    prediction = model.predict(X)[0]
    probability = model.predict_proba(X)[0]

    confidence = probability[prediction]

    return prediction, confidence


def choose_route(congestion):
    """
    Decide which path should be preferred.

    0 = Normal
    1 = Congested
    """

    if congestion == 1:
        return "r1 -> r2 -> r3"

    return "r1 -> r3"


def main():

    print("\n===================================")
    print("AI-Assisted OSPF Route Decision")
    print("===================================")

    # Example values taken from our latest
    # congested monitoring sample.
    sample = {
        "rx_rate": 0.209162,
        "tx_rate": 9.827728,
        "packet_rate": 522.88,
        "min_latency": 38.844,
        "max_latency": 51.949
    }

    model = load_model()

    prediction, confidence = predict_congestion(
        model,
        sample
    )

    route = choose_route(prediction)

    print(f"Congestion Prediction : {'CONGESTED' if prediction else 'NORMAL'}")
    print(f"Confidence            : {confidence * 100:.2f}%")
    print("-----------------------------------")
    print(f"Recommended Route     : {route}")
    print("===================================")


if __name__ == "__main__":
    main()
