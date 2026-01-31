# Entropy Analysis of ESP-Based Covert Channel

## 1. Objective

The objective of this experiment is to evaluate whether embedding covert data inside the **ESP padding field** introduces statistically detectable differences in packet randomness.

Specifically, the experiment compares the **byte-level entropy** of:

* ESP traffic **without covert data** (baseline)
* ESP traffic **with covert data embedded in padding** (covert)

If the covert channel is stealthy, the entropy of both traffic streams should remain statistically similar.

---

## 2. Experimental Setup

* **Sender VM:** Generates ESP packets (baseline or covert mode)
* **Receiver VM:** Captures ESP traffic and performs entropy analysis
* **Network:** Isolated IPv6 virtual network (`covert`)
* **Protocol Analyzed:** IPv6 ESP (Next Header = 50)

---

## 3. Traffic Generation (Sender Side)

The sender uses a modified ESP packet generator (`entropytx.py`) to produce high-volume ESP traffic.

Two execution modes are supported:

### Baseline Mode

No covert data is embedded in ESP padding.

```bash
sudo python3 entropytx.py --baseline
```

* Sends 10,000 ESP packets
* ESP padding contains only zero bytes
* Serves as reference traffic

---

### Covert Mode

Random covert data is embedded inside the ESP padding field.

```bash
sudo python3 entropytx.py --covert
```

* Sends 20,000 ESP packets
* Covert payload length varies randomly per packet
* Covert data is encrypted along with ESP payload
* Packets are protocol-compliant

---

## 4. Traffic Capture (Receiver Side)

On the receiver VM, ESP packets are captured using `tcpdump`.

### Baseline Traffic Capture

```bash
sudo tcpdump -i enp1s0 ip6 proto 50 -w baseline_traffic.pcap -c 1000
```

### Covert Traffic Capture

```bash
sudo tcpdump -i enp1s0 ip6 proto 50 -w covert_traffic.pcap -c 1000
```

These captures contain **only ESP packets**, ensuring analysis is limited to encrypted payload traffic.

---

## 5. Entropy Analysis Pipeline

Entropy analysis is automated using the script `entropy_test.sh`, executed on the receiver VM.

```bash
./entropy_test.sh
```

The script performs the following steps:

1. Reads baseline and covert PCAP files
2. Extracts ESP packet hex dumps using `tshark`
3. Converts packet hex data into raw binary streams
4. Computes entropy using the `ent` randomness test tool
5. Saves entropy results to log files

Generated files include:

* `baseline_entropy.log`
* `covert_entropy.log`

---

## 6. Sample Output

Representative entropy results are shown below.

### Baseline ESP Traffic

```
Entropy = 7.018045 bits per byte.
```

### Covert ESP Traffic

```
Entropy = 7.023259 bits per byte.
```

Both traffic streams exhibit entropy values close to the theoretical maximum of **8 bits per byte**.

---

## 7. Observations

* Baseline and covert ESP traffic show **nearly identical entropy**
* No statistically significant entropy increase is observed in covert traffic
* Encryption dominates byte-level randomness
* Covert data embedded in ESP padding does not introduce detectable entropy artifacts

Additional statistical indicators (chi-square, serial correlation, Monte Carlo Pi estimation) also remain comparable between the two traffic streams.

---

## 8 Interpretation

The results indicate that the covert channel implemented via ESP padding is **entropy-transparent**:

* Encrypted ESP traffic masks covert data effectively
* Padding-based covert data blends into encrypted payload
* Entropy-based detection methods are ineffective in distinguishing covert traffic from baseline traffic

This supports the feasibility of ESP padding as a **stealthy covert communication channel**.

---

## 9. Conclusion

This experiment demonstrates that:

* Covert data embedded in ESP padding does not significantly alter packet entropy
* Encrypted ESP traffic provides strong concealment
* Entropy analysis alone is insufficient to detect the covert channel
* The covert channel preserves protocol correctness and statistical invisibility

---

## 10. Reproducibility Notes

To reproduce this experiment:

1. Run `sender2.py` in baseline and covert modes
2. Capture ESP traffic using `tcpdump`
3. Execute `entropy_test.sh`
4. Compare `baseline_entropy.log` and `covert_entropy.log`

All steps are deterministic given the same traffic volume and configuration.
