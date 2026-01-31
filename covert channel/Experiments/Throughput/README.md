# Throughput Impact Analysis

## 1. Objective

The objective of this experiment is to evaluate the **impact of the ESP-based covert channel on network throughput**.

Specifically, the experiment examines whether the presence of continuous ESP covert traffic affects the achievable throughput of concurrent application-level traffic.

---

## 2. Experimental Setup

* **Sender VM:**

  * Generates ESP traffic using `sender.py`
  * Acts as the `iperf3` server
* **Receiver VM:**

  * Generates UDP traffic using `iperf3`
  * Runs the ESP receiver
* **Network:** Isolated IPv6 virtual network (`covert`)
* **Throughput Tool:** `iperf3`
* **Traffic Type:** UDP
* **Test Duration:** 60 seconds per run

ESP traffic and UDP throughput traffic share the same network interface, creating controlled contention.

---

## 3. Execution Methodology

---

### 3.1 Sender VM

On the sender VM, an `iperf3` server is started, followed by the ESP sender:

```bash
iperf3 -s
python3 sender.py
```

The ESP sender continuously transmits ESP packets during the throughput measurement.

---

### 3.2 Receiver VM

On the receiver VM, UDP traffic is generated using `iperf3`, and the ESP receiver is run in parallel:

```bash
iperf3 -c <RECEIVER_IP> -u -b <RATE> -t 60
time python3 receiver.py --covert
```

The experiment is repeated for three target UDP throughput rates:

* **10 Mbps**
* **50 Mbps**
* **100 Mbps**

Each run lasts exactly **60 seconds**.

---

## 4. Metrics Collected

For each throughput level, the following metrics are observed from `iperf3` output:

* Achieved bitrate (Mbps)
* Total data transferred
* Packet retransmissions (if any)
* Stability of throughput over time

---

## 5. Experimental Results

---

### 10 Mbps Throughput Test

**Observed Results:**

* Target bitrate: 10 Mbps
* Achieved bitrate: **10.0 Mbps**
* Total transfer: **71.6 MB**
* Retransmissions: Minimal

Both sender and receiver report consistent throughput across the full 60-second interval.

---

### 50 Mbps Throughput Test

**Observed Results:**

* Target bitrate: 50 Mbps
* Achieved bitrate: **50.0 Mbps**
* Total transfer: **358 MB**
* Retransmissions: Minimal

Throughput remains stable with no noticeable degradation due to ESP covert traffic.

---

### 100 Mbps Throughput Test

**Observed Results:**

* Target bitrate: 100 Mbps
* Achieved bitrate: **100 Mbps**
* Total transfer: **715 MB**
* Retransmissions: Very low

The system sustains high throughput even under heavy ESP traffic load.

---

## 6. Summary Table

| Target Rate | Achieved Throughput | Duration | Data Transferred |
| ----------- | ------------------- | -------- | ---------------- |
| 10 Mbps     | 10.0 Mbps           | 60 s     | 71.6 MB          |
| 50 Mbps     | 50.0 Mbps           | 60 s     | 358 MB           |
| 100 Mbps    | 100 Mbps            | 60 s     | 715 MB           |

---

## 7. Observations

* Achieved throughput closely matches the configured target rate in all tests
* Throughput remains stable over time
* ESP covert traffic does not introduce noticeable congestion
* No significant packet loss or jitter is observed
* Performance scales linearly with increased load

---

## 8. Interpretation

The results indicate that the ESP-based covert channel:

* Coexists efficiently with high-bandwidth application traffic
* Does not significantly reduce available throughput
* Introduces negligible contention even at **100 Mbps**
* Preserves normal network performance characteristics

This suggests that the covert channel remains **performance-transparent** under typical and high-load conditions.

---

## 9. Conclusion

This experiment demonstrates that:

* The ESP covert channel has **minimal impact on throughput**
* High-bandwidth UDP traffic is unaffected
* Covert communication remains stealthy even under heavy network load
* The covert channel does not degrade overall network performance

Combined with entropy, robustness, and RTT results, this confirms that the covert channel is **statistically invisible, resilient, and performance-efficient**.

---

## 10. Reproducibility Notes

To reproduce this experiment:

1. Start `iperf3 -s` on the sender VM
2. Run `sender.py` to generate ESP traffic
3. Start `iperf3` client on the receiver VM at the desired bitrate
4. Run `receiver.py` in parallel
5. Observe throughput statistics from `iperf3`

All tests should be run under similar system load for consistency.


