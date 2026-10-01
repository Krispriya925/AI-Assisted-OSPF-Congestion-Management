
import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    accuracy_score
)

# 1. Load labeled dataset
INPUT = "data/labeled_data.csv"
MODEL_OUTPUT = "models/congestion_model.pkl"

df = pd.read_csv(INPUT)

print("Dataset shape:", df.shape)
print("\nCongestion distribution:")
print(df["congestion"].value_counts().sort_index())

# 2. Select features
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

X = df[FEATURES]
y = df["congestion"]

# Check for invalid feature values
X = X.replace([float("inf"), float("-inf")], float("nan"))

# 3. Check whether a stratified split is possible
class_counts = y.value_counts()
rare_classes = class_counts[class_counts < 2]

if not rare_classes.empty:
    print("\nWARNING: Some classes have fewer than 2 samples:")
    print(rare_classes)
    print(
        "\nTraining on all available data for now. "
        "Holdout evaluation is skipped."
    )

    X_train = X
    y_train = y
    evaluate = False

else:
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )
    evaluate = True

print("\nTraining samples:", len(X_train))

if evaluate:
    print("Testing samples:", len(X_test))

# 4. Build a pipeline that handles missing measurements
model = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("rf", RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight="balanced"
    ))
])

# 5. Train
print("\nTraining Random Forest...")
model.fit(X_train, y_train)
print("[OK] Model training completed")

# 6. Evaluate only when a valid holdout split is available
if evaluate:
    y_pred = model.predict(X_test)

    print("\n==============================")
    print("MODEL EVALUATION")
    print("==============================")

    print("\nAccuracy:", accuracy_score(y_test, y_pred))

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred, labels=[0, 1, 2]))

    print("\nClassification Report:")
    print(classification_report(
        y_test,
        y_pred,
        labels=[0, 1, 2],
        target_names=["NORMAL", "CONGESTED", "CRITICAL"],
        zero_division=0
    ))
else:
    print("\nEvaluation skipped: insufficient samples in at least one class.")
    print("Do not treat training success as proof of model accuracy.")

# 7. Feature importance
importance = pd.DataFrame({
    "feature": FEATURES,
    "importance": model.named_steps["rf"].feature_importances_
}).sort_values("importance", ascending=False)

print("\nFeature Importance:")
print(importance.to_string(index=False))

# 8. Save model
os.makedirs("models", exist_ok=True)
joblib.dump(model, MODEL_OUTPUT)

print(f"\n[OK] Model saved to {MODEL_OUTPUT}")
