import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score


# --------------------------------------------------
# 1. Load labeled dataset
# --------------------------------------------------

INPUT = "data/labeled_data.csv"
MODEL_OUTPUT = "models/congestion_model.pkl"

df = pd.read_csv(INPUT)

print("Dataset shape:", df.shape)

print("\nCongestion distribution:")
print(df["congestion"].value_counts())


# --------------------------------------------------
# 2. Select ML features
# --------------------------------------------------

FEATURES = [
    "rx_rate",
    "tx_rate",
    "packet_rate",
    "min_latency",
    "max_latency"
]

X = df[FEATURES]
y = df["congestion"]


# --------------------------------------------------
# 3. Split dataset
# --------------------------------------------------

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))


# --------------------------------------------------
# 4. Create Random Forest model
# --------------------------------------------------

model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    class_weight="balanced"
)


# --------------------------------------------------
# 5. Train
# --------------------------------------------------

print("\nTraining Random Forest...")

model.fit(X_train, y_train)

print("[OK] Model training completed")


# --------------------------------------------------
# 6. Prediction
# --------------------------------------------------

y_pred = model.predict(X_test)


# --------------------------------------------------
# 7. Evaluation
# --------------------------------------------------

accuracy = accuracy_score(y_test, y_pred)

print("\n==============================")
print("MODEL EVALUATION")
print("==============================")

print("\nAccuracy:", accuracy)

print("\nConfusion Matrix:")
print(confusion_matrix(y_test, y_pred))

print("\nClassification Report:")
print(classification_report(y_test, y_pred))


# --------------------------------------------------
# 8. Feature importance
# --------------------------------------------------

print("\nFeature Importance:")

importance = pd.DataFrame({
    "feature": FEATURES,
    "importance": model.feature_importances_
})

importance = importance.sort_values(
    "importance",
    ascending=False
)

print(importance)


# --------------------------------------------------
# 9. Save model
# --------------------------------------------------

joblib.dump(model, MODEL_OUTPUT)

print(f"\n[OK] Model saved to {MODEL_OUTPUT}")
