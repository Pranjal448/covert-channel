# Memory (RAM) Overhead Analysis

## 1. Objective

The objective of this experiment is to measure the **memory (RAM) overhead** introduced by the covert channel during ESP packet generation.

The experiment compares:

* Memory usage of the sender process during **baseline ESP transmission**
* Memory usage of the sender process during **covert ESP transmission**

This analysis evaluates whether embedding covert data causes **noticeable or abnormal memory consumption**, which could act as a detection signal.

---

## 2. Experimental Setup

* **Host:** Ubuntu Linux virtual machine
* **Process under observation:** `python3 sender.py`
* **Monitoring tool:** `top`
* **Traffic mode:**

  * Baseline (no covert data)
  * Covert (random covert data in ESP padding)
* **Packet volume:** Continuous packet generation

The sender process is executed continuously while memory usage is observed in real time.

---

## 3. Measurement Methodology

1. The sender process is started in **baseline mode**
2. The `top` command is executed in parallel
3. Memory statistics for the sender process are recorded
4. The experiment is repeated for **covert mode**
5. Memory usage values are compared

Commands used:

```bash
sudo python3 sender.py --baseline
```

```bash
sudo python3 sender.py --covert
```

The `top` output is used to observe:

* **VIRT** (virtual memory size)
* **RES** (resident set size – actual RAM used)
* **MEM%** (percentage of system RAM)

---

## 4. Baseline Mode Memory Usage

During baseline ESP transmission:

* **Process:** `python3 sender.py --baseline`
* **Virtual Memory (VIRT):** ~65 MB
* **Resident Memory (RES):** ~51 MB
* **Memory Usage:** ~0.9%

The baseline process maintains stable memory usage throughout execution.

---

## 5. Covert Mode Memory Usage

During covert ESP transmission:

* **Process:** `python3 sender.py --covert`
* **Virtual Memory (VIRT):** ~65 MB
* **Resident Memory (RES):** ~51–52 MB
* **Memory Usage:** ~0.9%

Memory consumption remains nearly identical to baseline operation.

---

## 6. Comparative Summary

| Mode     | VIRT (MB) | RES (MB) | MEM%  |
| -------- | --------- | -------- | ----- |
| Baseline | ~65       | ~51      | ~0.9% |
| Covert   | ~65       | ~51–52   | ~0.9% |

---

## 7. Observations

* No noticeable increase in memory usage in covert mode
* Memory footprint remains stable across modes
* ESP encryption dominates memory allocation
* Covert data embedding does not trigger additional buffers or allocations
* No abnormal memory spikes observed

---

## 8. Interpretation

The memory analysis shows that:

* Covert padding manipulation is **memory-neutral**
* No additional long-lived data structures are created
* Covert communication does not alter the sender’s memory profile
* RAM usage remains consistent with normal ESP packet generation

This is important for stealth, as memory-based anomaly detection would be ineffective.

---

## 9. Conclusion

This experiment demonstrates that:

* The ESP-based covert channel introduces **negligible RAM overhead**
* Memory usage remains indistinguishable from baseline ESP operation
* The covert channel does not leak detectable signals via memory consumption

Together with RTT, throughput, entropy, and robustness results, this confirms that the covert channel is **performance- and resource-transparent**.

---

## 10. Reproducibility Notes

To reproduce this experiment:

1. Run the sender in baseline mode
2. Observe memory usage using `top` or `htop`
3. Repeat using covert mode
4. Compare RES and MEM% values for the sender process

Measurements should be taken after the process reaches steady state.
