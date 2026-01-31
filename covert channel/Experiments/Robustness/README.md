# Robustness Analysis under Packet Loss

## 1. Objective

The objective of this experiment is to evaluate the **robustness of the ESP-based covert channel** under adverse network conditions, specifically **packet loss**.

The experiment tests whether covertly transmitted data can be **successfully reconstructed** at the receiver when a fraction of ESP packets are randomly dropped by the network.


---

## 2. Experimental Setup

* **Sender VM:** Transmits covert data embedded in ESP padding
* **Receiver VM:** Captures ESP packets and reconstructs covert data
* **Network:** Isolated IPv6 virtual network (`covert`)
* **Packet Loss Injection:** Linux `tc netem`
* **Traffic Volume:** Exactly 1000 ESP packets per run
* **Test File:** `secret.txt`

---
Great catch — this is **exactly** the kind of clarification examiners and readers look for 👍
I’ll answer in two parts:

1. **What “X% packet loss” means (README-ready explanation)**
2. **Exactly where to put it in your existing README (best placement + why)**

---

## 3. Packet Loss Percentage Interpretation

In this experiment, packet loss is introduced using the Linux `tc netem` queuing discipline.

A packet loss rate of **X%** means that:

> On average, **X out of every 100 transmitted packets** are randomly dropped by the network before reaching the receiver.

For example:

* **1% packet loss** → approximately 1 packet dropped per 100 packets
* **3% packet loss** → approximately 3 packets dropped per 100 packets
* **5% packet loss** → approximately 5 packets dropped per 100 packets

Packet loss is applied **independently and randomly** to each packet.
There is no guarantee which specific packets are dropped, and consecutive losses may occur.

In this experiment:

* Exactly **1000 ESP packets** are transmitted per run
* Expected dropped packets are approximately:

  * ~10 packets at 1% loss
  * ~30 packets at 3% loss
  * ~50 packets at 5% loss

Actual packet loss may vary slightly due to randomness, as observed in receiver statistics.

---

## 4. Packet Loss Injection

Packet loss is introduced on the **sender VM** using Linux Traffic Control (`tc`) with the `netem` queuing discipline.

Before each run, any existing qdisc is cleared and a new packet loss rule is applied.

```bash
sudo tc qdisc del dev enp1s0 root 2>/dev/null
sudo tc qdisc add dev enp1s0 root netem loss <X>%
```

The experiment is conducted for the following packet loss rates:

* **1% loss**
* **3% loss**
* **5% loss**

The active configuration is verified using:

```bash
tc qdisc show dev enp1s0
```

---

## 5. Covert File Transmission (Sender Side)

The sender uses `robustness_Tx.py` to transmit a file covertly over ESP packets.

```bash
sudo python3 robustness_Tx.py --file secret.txt
```

### Sender Strategy

* The file is split into **small fixed-size chunks**
* Each chunk is embedded into ESP padding along with:

  * Chunk ID
  * End-of-file flag
* Each chunk is **repeated multiple times** across packets
* Dummy ESP packets are sent to reach exactly **1000 packets**

This repetition provides **implicit redundancy**, allowing recovery even when packets are lost.

Before transmission, the sender computes the file hash:

```bash
sha256sum secret.txt
```

This hash is later used to verify integrity at the receiver.

---

## 6. Receiver Operation

The receiver uses `robustness_Rx.py` to:

1. Sniff exactly 1000 ESP packets
2. Verify ESP integrity (HMAC-SHA1)
3. Decrypt ESP payloads (AES-CBC)
4. Extract covert data from ESP padding
5. Reassemble file chunks
6. Write the reconstructed file to disk
7. Compute SHA-256 hash of the reconstructed file

```bash
sudo python3 robustness_Rx.py
```

---

## 7. Experimental Results

The experiment is repeated three times under increasing packet loss rates.

---

### 1% Packet Loss

**Receiver statistics:**

* Packets seen: 989
* Valid ESP packets: 989
* Chunks stored: 2
* File reconstruction: **Successful**

**Integrity check:**

```bash
Original SHA-256    = 5bb35ea40fa62f692892283aef8ff2a8799bf329798f651d1cbc9d64503ad244
Reconstructed SHA-256 = 5bb35ea40fa62f692892283aef8ff2a8799bf329798f651d1cbc9d64503ad244
```
* Original SHA-256 = Reconstructed SHA-256
* No data corruption observed

---

### 3% Packet Loss

**Receiver statistics:**

* Packets seen: 977
* Valid ESP packets: 977
* Chunks stored: 2
* File reconstruction: **Successful**

**Integrity check:**

```bash
Original SHA-256    = 5bb35ea40fa62f692892283aef8ff2a8799bf329798f651d1cbc9d64503ad244
Reconstructed SHA-256 = 5bb35ea40fa62f692892283aef8ff2a8799bf329798f651d1cbc9d64503ad244
```
* Original SHA-256 = Reconstructed SHA-256
* Covert data fully recovered despite higher loss

---

### 5% Packet Loss

**Receiver statistics:**

* Packets seen: 959
* Valid ESP packets: 959
* Chunks stored: 2
* File reconstruction: **Successful**

**Integrity check:**

```bash
Original SHA-256    = 5bb35ea40fa62f692892283aef8ff2a8799bf329798f651d1cbc9d64503ad244
Reconstructed SHA-256 = 5bb35ea40fa62f692892283aef8ff2a8799bf329798f651d1cbc9d64503ad244
```
* Original SHA-256 = Reconstructed SHA-256
* Covert channel remains functional under significant loss

---

## 8. Observations

* Increasing packet loss reduces the number of received ESP packets
* ESP integrity verification remains intact for all received packets
* Redundant chunk transmission enables full file recovery
* Covert data reconstruction succeeds even at **5% packet loss**
* Packet loss does not break synchronization or chunk ordering

---

## 9. Interpretation

This experiment demonstrates that the covert channel is **robust to moderate packet loss**:

* ESP encryption and authentication remain unaffected
* Padding-based covert data survives lossy conditions
* Simple redundancy provides strong resilience
* No explicit retransmission or acknowledgment protocol is required

The design naturally tolerates packet loss due to repeated chunk embedding.

---

## 10. Conclusion

The robustness experiment confirms that:

* The ESP-based covert channel can reliably transmit files under packet loss
* Covert communication remains intact at up to **5% packet loss**
* Data integrity is preserved, as verified by SHA-256 hashes
* The covert channel is suitable for unreliable network environments

This strengthens the practicality of ESP padding as a resilient covert communication mechanism.

---

## 11. Reproducibility Notes

To reproduce this experiment:

1. Apply packet loss using `tc netem`
2. Run `robustness_Tx.py --file <file>`
3. Run `robustness_Rx.py` simultaneously
4. Compare SHA-256 hashes of original and reconstructed files
5. Repeat for different packet loss rates

