# RTT Impact Analysis of the Covert Channel

## 1. Objective

The objective of this experiment is to measure the **impact of the ESP-based covert channel on network latency**, specifically **Round-Trip Time (RTT)**.

The experiment compares:

* RTT under **baseline ESP traffic** (no covert data)
* RTT under **covert ESP traffic** (ESP padding carries covert data)

The goal is to determine whether the covert channel introduces **measurable latency overhead** on normal network traffic.

---

## 2. Experimental Setup

* **Sender VM:** Generates continuous ESP traffic (baseline or covert)
* **Receiver VM:** Receives ESP packets
* **Network:** Isolated IPv6 virtual network (`covert`)
* **Traffic Type Under Test:** ICMPv6 Echo (ping)
* **Measurement Tool:** `ping`
* **Sample Size:** 60 ICMP echo requests per run

ESP traffic and ICMP traffic share the same virtual network interface.

---

## 3. Execution Methodology

The experiment is conducted in two phases.

---

### 3.1 Receiver Startup

On the receiver VM, the ESP receiver is started first:

```bash
sudo python3 receiver.py
```

This ensures that ESP traffic generated during the experiment is properly received and processed.

---

### 3.2 Baseline RTT Measurement

On the sender VM, baseline ESP traffic is generated in parallel with ICMPv6 echo requests.

```bash
sudo python3 RTT_Tx.py --baseline
ping 2001:db8:100::20 -c 60
```

* ESP packets contain **no covert data**
* ICMP RTT is measured while ESP traffic is active
* 60 echo requests are sent to compute RTT statistics

---

### 3.3 Covert RTT Measurement

The experiment is repeated with covert data embedded in ESP padding:

```bash
sudo python3 RTT_Tx.py --covert
ping 2001:db8:100::20 -c 60
```

* ESP packets carry covert data
* ICMP RTT is measured under covert channel operation
* Same number of echo requests ensures fair comparison

---

## 4. Metrics Collected

For each run, the following RTT metrics are collected from `ping` output:

* **Minimum RTT**
* **Average RTT**
* **Maximum RTT**
* **Mean Deviation (mdev)**

All values are reported in milliseconds (ms).

---

## 5 Experimental Results

---

### 5.1 Baseline RTT Results

```
rtt min/avg/max/mdev = 0.160/0.315/1.652/0.234 ms
```

**Observations:**

* Low average RTT
* Minimal variance
* Stable latency under baseline ESP traffic

---

### 5.2 Covert RTT Results

```
rtt min/avg/max/mdev = 0.156/0.432/3.742/0.522 ms
```

**Observations:**

* Slight increase in average RTT
* Higher maximum RTT and variance
* Latency remains within sub-millisecond range for most packets

---

## 6. Comparative Analysis

| Metric              | Baseline (ms) | Covert (ms) |
| ------------------- | ------------- | ----------- |
| Minimum RTT         | 0.160         | 0.156       |
| Average RTT         | 0.315         | 0.432       |
| Maximum RTT         | 1.652         | 3.742       |
| RTT Variance (mdev) | 0.234         | 0.522       |

---

## 7. Interpretation

* The covert channel introduces a **small increase in average RTT**
* The increase is attributable to:

  * Additional cryptographic processing
  * Increased packet size due to covert padding
* RTT variability increases slightly under covert traffic
* No packet loss or timeout is observed

Importantly, the observed RTT values remain **well within acceptable limits** for typical network applications.

---

## 8. Conclusion

This experiment demonstrates that:

* The ESP-based covert channel has **minimal impact on RTT**
* Latency overhead is small and unlikely to raise suspicion
* Normal network services remain usable during covert communication
* The covert channel maintains stealth not only statistically but also performance-wise

---

## 9. Reproducibility Notes

To reproduce this experiment:

1. Start `receiver.py` on the receiver VM
2. Run `RTT_Tx.py` in baseline mode while measuring RTT using `ping`
3. Repeat using covert mode
4. Compare RTT statistics reported by `ping`

All measurements should be taken under similar system load for consistency.
