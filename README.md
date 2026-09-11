# AI-Assisted OSPF Congestion Management

An AI-assisted networking project that monitors an OSPF-based network, extracts network-health metrics, predicts congestion using a Machine Learning model, and recommends an alternate path when congestion is detected.

> **Current documented topology:** 3 routers (`r1`, `r2`, `r3`) with two end hosts (`h1`, `h2`).
>
> The newer 6-router topology is intentionally **excluded** from this README because the current project documentation and completed workflow are based on the original 3-router topology.

---

## 1. Project Overview

Traditional OSPF selects routes mainly using its routing metric/cost. In this project, network monitoring data is used to identify congestion and support an **AI-aware path recommendation**.

The current workflow is:

```text
Mininet + FRR/OSPF
        ↓
Network Monitoring
        ↓
Data Preprocessing
        ↓
Feature Engineering
        ↓
Congestion Labeling
        ↓
Random Forest Prediction
        ↓
K-Shortest Path Generation
        ↓
Path Cost / Congestion-Aware Evaluation / Health score
        ↓
Best Path Recommendation
```

The current implementation is a **route recommendation system**. It does not yet automatically modify the real OSPF routing table.

---

## 2. Current Architecture

```text
                    ┌──────────────────────────┐
                    │     Mininet + FRR/OSPF   │
                    │       Network/Testbed    │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │      Data Collection     │
                    │ RX/TX bytes & packets    │
                    │ RX/TX rates              │
                    │ Packet rate              │
                    │ Min/Avg/Max latency      │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Preprocessing & Features │
                    │ Cleaning                 │
                    │ Rate calculation         │
                    │ Packet-rate calculation  │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Random Forest Classifier │
                    │ 0 = Normal               │
                    │ 1 = Congested            │
                    └────────────┬─────────────┘
                                 │
                          Congestion detected?
                           /              \
                         No                Yes
                         │                  │
                         ▼                  ▼
                   Keep monitoring   Generate candidate
                                     alternate paths
                                            │
                                            ▼
                                     Path selection


                                     OSPF Network


The overall flow

             ↓
        Mininet + FRRouting
             ↓
        Network Monitoring
             ↓
        Raw Metrics
        (RX/TX, Packet Rate, Latency)
             ↓
        Data Preprocessing
             ↓
        Feature Engineering
             ↓
        Congestion Prediction
        (Random Forest)
             ↓
        ┌───────────────────────┐
        │ Congestion Detected?  │
        └───────────┬───────────┘
               No   │   Yes
               ↓    │    ↓
          Keep      │  K-Shortest
        Monitoring  │    Paths
               ↑    │    ↓
               │    │  Path Health
               │    │  Evaluation
               │    │    ↓
               │    │  Health Score
               │    │    ↓
               │    │  Rank Paths
               │    │    ↓
               │    │  Best Path
               │    │    ↓
               │    │  Route
               │    │  Recommendation
               │    │    ↓
               │    │  SHAP Explanation
               │    │    ↓
               │    │  Proposed OSPF
               │    │    Update
               │    │    ↓
               └────┴─ Continuous
                     Feedback Loop
```

---

## 3. Original 3-Router Topology

The project originally uses three routers and two hosts.

```text
                         r2
                       /    \
                      /      \
                    r1 ------ r3
                    |          |
                   h1          h2
```

### Links

- `h1 ↔ r1`
- `r1 ↔ r2`
- `r1 ↔ r3`
- `r2 ↔ r3`
- `r3 ↔ h2`

This topology provides two possible router-level paths from `r1` to `r3`:

```text
Path 1:
r1 → r3

Path 2:
r1 → r2 → r3
```

This is the topology used by the current path-selection prototype.

---

## 4. OSPF Network Configuration

The network is implemented using:

- **Mininet** — network emulation
- **FRRouting (FRR)** — routing software
- **OSPF** — link-state routing protocol
- **NetworkX** — graph/path processing
- **Python** — project implementation

### Router IDs

| Router | OSPF Router ID |
|--------|----------------|
|   r1   | `1.1.1.1`      |
|   r2   | `2.2.2.2`      |
|   r3   | `3.3.3.3`      |

### Main IP addressing

| Device | Interface | IP             |
|--------|-----------|----------------|
| r1     | r1-eth0   | `10.0.1.254/24`|
| r1     | r1-eth1   | `10.0.12.1/24` |
| r1     | r1-eth2   | `10.0.13.1/24` |
| r2     | r2-eth0   | `10.0.12.2/24` |
| r2     | r2-eth1   | `10.0.23.1/24` |
| r3     | r3-eth0   | `10.0.13.2/24` |
| r3     | r3-eth1   | `10.0.23.2/24` |
| r3     | r3-eth2   | `10.0.3.254/24`|
| h1     | h1-eth0   | `10.0.1.1/24`  |
| h2     | h2-eth0   | `10.0.3.1/24`  |

OSPF is configured in **Area 0**.

---

## 5. OSPF Verification

The OSPF implementation has been verified inside Mininet.

### Neighbor formation

`r1` successfully forms OSPF neighbor relationships with:

```text
2.2.2.2
3.3.3.3
```

The routing table also shows OSPF-learned routes.

For example, the original topology selected:

```text
10.0.3.0/24
via 10.0.13.2
dev r1-eth2
```

This confirms that the normal OSPF path from `r1` toward the `h2` network is through `r3`.

### End-to-end connectivity

The original topology has also been tested using:

```text
h1 ping 10.0.3.1
```

and successful packet delivery was observed.

---

# 6. Network Monitoring

## `scripts/monitor.py`

The monitoring component collects network statistics from the Mininet environment.

It uses:

- `ip -s link`
- `ping`

### Collected metrics

The monitoring pipeline records:

- RX bytes
- RX packets
- TX bytes
- TX packets
- Minimum latency
- Average latency
- Maximum latency
- Timestamp

The data is continuously appended to:

```text
data/network_data.csv
```

The monitor runs periodically and can be stopped with:

```text
Ctrl+C
```

---

# 7. Data Preprocessing

## `scripts/preprocess.py`

The preprocessing stage reads:

```text
data/network_data.csv
```

and produces:

```text
data/processed_data.csv
```

### Current preprocessing operations

1. Load raw monitoring data
2. Convert timestamps
3. Remove duplicate rows
4. Remove missing values
5. Sort the data chronologically
6. Save the processed dataset

---

# 8. Feature Engineering

## `scripts/features.py`

The feature-engineering stage converts cumulative network counters into useful rate-based features.

### Calculated features

The current feature dataset contains:

```text
timestamp
rx_rate
tx_rate
packet_rate
min_latency
avg_latency
max_latency
latency
```

### Rate calculations

RX and TX byte counters are converted into Mbps using the time difference between measurements.

Packet rate is calculated as packets per second.

The main latency feature is currently:

```text
latency = avg_latency
```

The resulting feature dataset is stored in:

```text
data/features.csv
```

---

# 9. Congestion Labeling

## `scripts/label_data.py`

The labeling stage creates the target variable used for ML training.

Current definition:

```text
0 = Normal
1 = Congested
```

The current prototype uses average latency as the congestion criterion:

```text
avg_latency > 1.0 ms
        ↓
Congested = 1
```

Otherwise:

```text
Congested = 0
```

The resulting dataset is:

```text
data/labeled_data.csv
```

The labeled dataset contains:

```text
timestamp
rx_rate
tx_rate
packet_rate
min_latency
avg_latency
max_latency
latency
congestion
```

---

# 10. Machine Learning Congestion Prediction

## `scripts/predict.py`

A Random Forest model is used to predict whether the current network condition is congested.

The prediction output includes:

```text
Prediction
Confidence
```

Example observed output:

```text
Prediction    : CONGESTED
Confidence    : 100.00%
```

The model is stored at:

```text
models/congestion_model.pkl
```

The current prediction pipeline uses network-health features such as:

- RX rate
- TX rate
- Packet rate
- Minimum latency
- Maximum latency

The prediction component has been successfully tested with the collected feature data.

---

# 11. AI-Aware Path Selection

## `scripts/path_selection.py`

The path-selection component integrates the congestion prediction with a graph representation of the original topology.

NetworkX is used to represent the topology.

Current graph:

```text
r1 ---- r2
 |    /
 |   /
 |  /
 r3
```

More precisely, all three router links exist:

```text
r1 ↔ r2
r1 ↔ r3
r2 ↔ r3
```

Each link initially has:

```text
cost = 10
congested = False
```

---

## 12. K-Shortest Paths

The current implementation uses NetworkX's shortest-simple-path functionality to generate candidate paths.

For the original topology and source/destination:

```text
Source      : r1
Destination : r3
```

the relevant candidate paths include:

```text
r1 → r3

r1 → r2 → r3
```

The project currently evaluates these candidate paths using the graph cost.

---

# 13. Congestion Penalty

The current prototype applies an additional penalty when a link is marked congested.

```text
CONGESTION_PENALTY = 100
```

For a congested link:

```text
Final Link Cost =
Original Cost + Congestion Penalty
```

For example:

```text
r1 → r3

Normal cost:
10

Congested cost:
10 + 100 = 110
```

The alternate path:

```text
r1 → r2 → r3
```

has:

```text
10 + 10 = 20
```

Therefore, when the direct `r1-r3` link is predicted as congested, the current prototype recommends:

```text
r1 → r2 → r3
```

---

# 14. Current Integrated Demonstration

The current implementation successfully produces the following type of decision:

```text
==============================
AI CONGESTION DECISION
==============================
Prediction : CONGESTED
Confidence : 100.00%
Congestion detected!
Applying penalty to R1-R3 link.

==============================
AI-AWARE PATH SELECTION
==============================
Path 1: r1 -> r3
Final Cost: 110

Path 2: r1 -> r2 -> r3
Final Cost: 20

------------------------------
SELECTED PATH: r1 -> r2 -> r3
SELECTED COST: 20
------------------------------
```

This demonstrates the completed connection between:

```text
ML congestion prediction
        ↓
congestion-aware link penalty
        ↓
candidate path evaluation
        ↓
alternate route recommendation
```

---

# 15. Route Decision Prototype

## `routing/route_decision.py`

There is also a route-decision prototype that directly connects the trained Random Forest model with a simple route decision.

Current logic:

```text
If congestion = 1
    → recommend r1 → r2 → r3

If congestion = 0
    → recommend r1 → r3
```

Example:

```text
Congestion Prediction : CONGESTED
Confidence            : 100.00%
Recommended Route     : r1 -> r2 -> r3
```

This component demonstrates the basic AI-to-routing decision logic.

The more flexible `scripts/path_selection.py` implementation is the current direction because it evaluates candidate paths instead of using only a hard-coded route choice.

---

# 16. What Has Been Completed

### Network/Testbed

- [x] Mininet topology created
- [x] Original 3-router topology implemented
- [x] FRRouting installed/configured
- [x] OSPF configured
- [x] OSPF neighbor formation verified
- [x] OSPF routes verified
- [x] End-to-end host connectivity tested

### Data Pipeline

- [x] Network monitoring
- [x] Raw CSV data collection
- [x] Data preprocessing
- [x] Feature engineering
- [x] Congestion labeling
- [x] Labeled dataset generation

### Machine Learning

- [x] Random Forest congestion classifier
- [x] Trained model saved as `models/congestion_model.pkl`
- [x] Congestion prediction tested
- [x] Prediction confidence generated

### Path Selection

- [x] NetworkX topology representation
- [x] Candidate path generation
- [x] Path cost calculation
- [x] Congestion penalty mechanism
- [x] AI prediction integrated with path selection
- [x] Best-path recommendation demonstrated

---

# 17. What Is NOT Completed Yet

The following are part of the planned architecture but are **not yet implemented as a complete system**:

- [ ] Health score calculation for every candidate path
- [ ] Evaluation using multiple path-health factors
- [ ] Dynamic path ranking based on health score
- [ ] Continuous closed-loop re-evaluation
- [ ] Automatic OSPF metric/update mechanism
- [ ] Automatic traffic forwarding through the AI-selected path
- [ ] SHAP explainability integration
- [ ] Dashboard/UI
- [ ] Full feedback loop
- [ ] Large multi-path topology evaluation

In particular, **health-score-based K-shortest-path evaluation is the next major path-selection step**.

---

# 18. Current Project Boundary

The project currently focuses on:

```text
Monitor
   ↓
Predict congestion
   ↓
Generate candidate paths
   ↓
Evaluate path cost
   ↓
Recommend the best path
```

It should currently be described as:

> **AI-assisted OSPF route recommendation / congestion-aware path selection**

rather than claiming that the AI is already directly controlling OSPF.

---

# 19. Planned Next Step

The next implementation stage is to replace the simple binary congestion penalty approach with a **Path Health Score**.

Conceptually:

```text
                    Candidate Path
                          │
          ┌───────────────┼────────────────┐
          ▼               ▼                ▼
   Congestion        Latency          Path Load/
   Prediction                        Utilization
          │               │                │
          └───────────────┼────────────────┘
                          ▼
                  Path Health Score
                          │
                          ▼
                 Rank Candidate Paths
                          │
                          ▼
                  Select Best Path
```

The health score will allow different candidate paths to be compared using more than only OSPF cost.

The intended factors include:

- Congestion prediction
- Average latency
- Path load/utilization
- Available bandwidth
- Hop count / OSPF cost

The exact weighting/formula will be defined during the next implementation stage.

---

# 20. Project Directory

Current relevant structure:

```text
AI-Assisted-OSPF-Congestion-Management/
│
├── ospf_topology.py
│
├── scripts/
│   ├── monitor.py
│   ├── preprocess.py
│   ├── features.py
│   ├── label_data.py
│   ├── predict.py
│   └── path_selection.py
│
├── routing/
│   └── route_decision.py
│
├── models/
│   └── congestion_model.pkl
│
├── data/
│   ├── network_data.csv
│   ├── processed_data.csv
│   ├── features.csv
│   └── labeled_data.csv
│
└── README.md
```

---

# 21. Basic Execution

## Activate the virtual environment

```bash
source .venv/bin/activate
```

The normal Python/ML components can then be executed with:

```bash
python scripts/predict.py
```

and:

```bash
python scripts/path_selection.py
```

The Mininet/FRR topology requires root privileges and is currently run using the system Python installation that has Mininet available:

```bash
sudo python3 ospf_topology.py
```

---

## 22. Summary

The project has progressed from a basic OSPF Mininet testbed to an AI-assisted congestion-aware routing prototype.

The completed pipeline is:

```text
Mininet + FRR
      ↓
OSPF Network
      ↓
Network Monitoring
      ↓
Raw Network Data
      ↓
Preprocessing
      ↓
Feature Engineering
      ↓
Congestion Labels
      ↓
Random Forest
      ↓
Congestion Prediction
      ↓
K-Shortest Candidate Paths
      ↓
Congestion-Aware Path Cost
      ↓
Best Route Recommendation
```

The **next major milestone** is to implement **Path Health Score-based evaluation** so that candidate paths are ranked according to their overall health rather than only applying a fixed congestion penalty.