# Repository Structure

This repository is organized to clearly separate the **core covert channel implementation** from the **individual experimental evaluations**.
Each experiment is self-contained, with separate sender (VM1) and receiver (VM2) code and its own documentation.

---

## Directory Tree Overview

```
.
├── covert channel
│   ├── Experiments
│   │   ├── Entropy
│   │   │   ├── README.md
│   │   │   ├── VM1
│   │   │   │   └── entropy_tx.py
│   │   │   └── VM2
│   │   │       ├── entropy_test.sh
│   │   │       └── receiver.py
│   │   ├── RAM
│   │   │   ├── README.md
│   │   │   ├── VM1
│   │   │   │   └── sender.py
│   │   │   └── VM2
│   │   │       └── receiver.py
│   │   ├── Robustness
│   │   │   ├── README.md
│   │   │   ├── Secret.txt
│   │   │   ├── VM1
│   │   │   │   └── robustness_Tx.py
│   │   │   └── VM2
│   │   │       └── robustness_Rx.py
│   │   ├── RTT
│   │   │   ├── README.md
│   │   │   ├── VM1
│   │   │   │   └── RTT_Tx.py
│   │   │   └── VM2
│   │   │       └── receiver.py
│   │   └── Throughput
│   │       ├── README.md
│   │       ├── VM1
│   │       │   └── sender.py
│   │       └── VM2
│   │           └── receiver.py
│   ├── README.md
│   ├── VM1
│   │   └── sender.py
│   └── VM2
│       └── receiver.py
└── ReadMe.md
```

-
