import csv
import re
import subprocess
import sys
import time
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
PYTHON = sys.executable

DATA_FILE = PROJECT_DIR / "data" / "network_data.csv"
MODEL_FILE = PROJECT_DIR / "models" / "congestion_model.pkl"

CHECK_INTERVAL = 2
CONGESTION_STATES = {"CONGESTED", "CRITICAL"}

monitor_process = None
last_processed_signature = None


def run_script(name, script):
    """Run one project script and stop if it fails."""
    script_path = PROJECT_DIR / script

    if not script_path.is_file():
        raise FileNotFoundError(f"Script not found: {script}")

    print(f"\n[RUNNING] {name}", flush=True)

    result = subprocess.run(
        [PYTHON, str(script_path)],
        cwd=PROJECT_DIR,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"{name} failed with exit code {result.returncode}"
        )

    print(f"[OK] {name} completed.", flush=True)


def read_latest_timestamp():
    """Return the newest timestamp in the raw monitoring CSV."""
    if not DATA_FILE.exists():
        return None

    try:
        with DATA_FILE.open(
            "r", newline="", encoding="utf-8"
        ) as file:
            rows = list(csv.DictReader(file))

        if not rows:
            return None

        return rows[-1].get("timestamp")

    except (OSError, csv.Error):
        return None


def get_prediction():
    """Run the existing prediction script and read its output."""
    script_path = PROJECT_DIR / "scripts" / "predict.py"

    result = subprocess.run(
        [PYTHON, str(script_path)],
        cwd=PROJECT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )

    print(result.stdout, end="", flush=True)

    if result.returncode != 0:
        raise RuntimeError("Congestion prediction failed.")

    match = re.search(
        r"Prediction\s*:\s*(NORMAL|CONGESTED|CRITICAL)",
        result.stdout,
        re.IGNORECASE,
    )

    if not match:
        raise RuntimeError(
            "Could not identify the prediction in predict.py output. "
            "Check the prediction script's output format."
        )

    return match.group(1).upper()


def analyze_paths():
    """Display candidate paths and recommend the best path."""
    run_script(
        "Candidate Path Generation",
        "scripts/topology_graph.py",
    )

    run_script(
        "Path Health Analysis and Recommendation",
        "scripts/path_selection.py",
    )


def start_monitor():
    """Start the existing monitor as a background process."""
    global monitor_process

    monitor_script = PROJECT_DIR / "scripts" / "monitor.py"

    if not monitor_script.is_file():
        raise FileNotFoundError("scripts/monitor.py was not found.")

    print("\n[MONITOR] Starting network monitoring...", flush=True)

    monitor_process = subprocess.Popen(
        [PYTHON, str(monitor_script)],
        cwd=PROJECT_DIR,
    )

    time.sleep(2)

    if monitor_process.poll() is not None:
        raise RuntimeError(
            "monitor.py exited unexpectedly. "
            "Check its error output and verify that the Mininet "
            "topology is running."
        )


def main():
    global last_processed_signature

    print("=" * 65)
    print("AI-ASSISTED OSPF CONGESTION MANAGEMENT")
    print("CONTINUOUS MONITORING MODE")
    print("=" * 65)

    try:
        # Prepare the existing dataset and train the model once.
        run_script("Data Preprocessing", "scripts/preprocess.py")
        run_script("Feature Engineering", "scripts/features.py")
        run_script("Congestion Labeling", "scripts/label_data.py")
        run_script(
            "Initial Model Training",
            "scripts/train_model.py",
        )

        start_monitor()

        # Ignore old measurements; process only newly recorded samples.
        last_processed_signature = read_latest_timestamp()

        print(
            "\n[MONITOR] Waiting for fresh network measurements...",
            flush=True,
        )

        while True:
            if monitor_process.poll() is not None:
                raise RuntimeError(
                    "The monitoring process stopped unexpectedly."
                )

            timestamp = read_latest_timestamp()

            if timestamp and timestamp != last_processed_signature:
                last_processed_signature = timestamp

                print("\n" + "=" * 65, flush=True)
                print(
                    f"[MONITOR] New measurement: {timestamp}",
                    flush=True,
                )

                # Update the features before predicting.
                run_script(
                    "Update Processed Dataset",
                    "scripts/preprocess.py",
                )
                run_script(
                    "Update Features",
                    "scripts/features.py",
                )

                prediction = get_prediction()

                if prediction in CONGESTION_STATES:
                    print(
                        f"\n[ALERT] {prediction} congestion detected!",
                        flush=True,
                    )

                    analyze_paths()

                    print(
                        "\n[MONITOR] Recommendation displayed. "
                        "Monitoring continues.",
                        flush=True,
                    )
                else:
                    print(
                        "\n[STATUS] Network condition is NORMAL. "
                        "No new path recommendation needed.",
                        flush=True,
                    )

            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n[STOP] Stopping continuous monitoring...", flush=True)

    except (RuntimeError, FileNotFoundError) as error:
        print(f"\n[ERROR] {error}", file=sys.stderr, flush=True)
        sys.exit(1)

    finally:
        if monitor_process and monitor_process.poll() is None:
            monitor_process.terminate()

            try:
                monitor_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                monitor_process.kill()
                monitor_process.wait()

        print("[STOP] Pipeline stopped.", flush=True)


if __name__ == "__main__":
    main()
