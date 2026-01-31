# IPSEC-Covert-Channel


## Virtual Machine Setup and Network Configuration

### 1. Overview

This project was developed and tested using a virtualized environment to ensure isolation, reproducibility, and controlled networking. Two Ubuntu virtual machines were created on a single Ubuntu host system using native Linux virtualization tools.

---

// steps to open virtual machine

## 2. Host System Details

* **Host Operating System:** Ubuntu Linux
* **Virtualization Interface:** virt-manager (Virtual Machine Manager)
* **Underlying Hypervisor:** KVM/QEMU

`virt-manager` is a graphical management tool for KVM-based virtual machines and uses `libvirt` to handle virtual hardware and networking.

---

## 3. Virtual Machine Creation

Two separate Ubuntu virtual machines were created to simulate a multi-node setup. One VM acts as sender VM, other acts as a receiver VM.

### 3.1 Guest Operating Systems

| VM Name | OS              | Architecture |
| ------- | --------------- | ------------ |
| VM1     | Ubuntu (64-bit) | x86_64       |
| VM2     | Ubuntu (64-bit) | x86_64       |

### 3.2 Common VM Configuration

* **CPU:** 1 vCPU
* **Memory:** 5.6 GiB
* **Disk:** 25 GB (QCOW2 format)

Each virtual machine was installed independently using the standard Ubuntu installer.

---

## 4. Network Configuration

### 4.1 Network Type

A custom isolated virtual IPv6 network named **covert** was created using libvirt via virt-manager. This network is attached to both virtual machines to provide private inter-VM communication while remaining isolated from the host system and external networks.


---

### 4.2 Manual IPv6 Configuration Using `link.sh`

#### Overview

Each virtual machine uses a shell script named `link.sh` to manually configure IPv6 networking on the isolated virtual network (`covert`).
The script is executed inside the VM to assign a **static IPv6 address** to the network interface, enabling deterministic and reproducible communication between the two VMs.

This approach avoids reliance on automatic IPv6 mechanisms such as SLAAC or DHCPv6.

---

#### Purpose of `link.sh`

The `link.sh` script performs the following high-level tasks:

1. Activates the network interface attached to the isolated network
2. Assigns a predefined static IPv6 address to the interface
3. Verifies the IPv6 configuration
4. Prepares the VM for IPv6-based communication with the peer VM

Separate scripts are used on each VM, with unique IPv6 addresses assigned to prevent conflicts.

---

#### Sender VM (VM1)

* **Network Interface:** `enp1s0`
* **Assigned IPv6 Address:** `2001:db8:100::10/64`
* **Role:** Acts as the sender in IPv6 communication tests

After configuration, VM1 is able to initiate IPv6 connectivity checks (e.g., ICMPv6 echo requests) to VM2.

---

#### Receiver VM (VM2)

* **Network Interface:** `enp1s0`
* **Assigned IPv6 Address:** `2001:db8:100::20/64`
* **Role:** Acts as the receiver in IPv6 communication tests

VM2 listens for incoming IPv6 traffic and can also initiate connectivity checks to VM1.

---

#### IPv6 Addressing Scheme

* **IPv6 Prefix:** `2001:db8:100::/64`
* **Address Type:** Static
* **Purpose:** Experimental / documentation-only IPv6 addressing

Using static addresses ensures predictable endpoints and simplifies testing and analysis.

---

#### Execution and Usage

The script is executed manually on each VM:

```bash
chmod +x link.sh
./link.sh
```

Once executed on both VMs, IPv6 connectivity can be verified using `ping6` between the assigned addresses.

---

#### Design Considerations

* Ensures full control over IPv6 addressing
* Avoids dynamic address assignment variability
* Suitable for isolated and secure VM environments
* Configuration is temporary and applies only for the current session
* Keeps permanent network configuration unchanged

---

#### Outcome

After running `link.sh` on both virtual machines:

* Each VM has a unique, known IPv6 address
* IPv6 communication is enabled over the isolated network
* VM-to-VM connectivity can be reliably tested

---

#### Note

The IPv6 configuration applied by `link.sh` is **non-persistent** and must be re-applied after a reboot. Persistent configuration would require changes to the system’s network configuration files (e.g., netplan).


---

### 5. ESP-Based Sender and Receiver Implementation

#### 5.1 Overview

After establishing IPv6 connectivity between the two virtual machines, the project implements an **IPsec ESP–based communication mechanism** to study the feasibility of a **padding-based covert channel**.

Two Python programs are used:

* `sender.py` — runs on the sender VM (VM1)
* `receiver.py` — runs on the receiver VM (VM2)

Both programs operate directly at the packet level and communicate over the isolated IPv6 network.

---

#### 5.2 Libraries Used

This project relies on a combination of **packet manipulation** and **cryptographic** libraries to manually construct, transmit, encrypt, decrypt, and analyze ESP packets.

---

##### Scapy

**Used in:** `sender.py`, `receiver.py`

Scapy is a powerful Python-based packet manipulation library that allows direct construction, transmission, and inspection of network packets.

**Usage in this project:**

* Construct Ethernet, IPv6, and UDP packets
* Manually encapsulate ESP payloads inside IPv6 packets
* Transmit raw packets at Layer 2 from the sender VM
* Sniff and capture ESP packets on the receiver VM

Scapy enables full control over packet structure, which is essential for implementing and analyzing covert channels at the protocol level.

---

##### PyCryptodome (Cryptodome)

**Used in:** `sender.py`, `receiver.py`

PyCryptodome provides cryptographic primitives required to implement ESP encryption and authentication.

---

##### AES (Advanced Encryption Standard)

**Module:**

```
Cryptodome.Cipher.AES
```

**Usage in this project:**

* Encrypt ESP payloads using **AES in CBC mode**
* Decrypt received ESP payloads on the receiver
* Ensure confidentiality of the encapsulated inner packet

AES-CBC is used to closely model the encryption behavior of real IPsec ESP implementations.

---

##### HMAC with SHA-1

**Module:**

```
Cryptodome.Hash.HMAC
Cryptodome.Hash.SHA1
```

**Usage in this project:**

* Compute an **Integrity Check Value (ICV)** for ESP packets
* Verify integrity and authenticity of received packets
* Detect packet modification or forgery

HMAC-SHA1 ensures that covert communication does not bypass ESP integrity protection.

---

##### Cryptographically Secure Random Number Generation

**Module:**

```
Cryptodome.Random.get_random_bytes
```

**Usage in this project:**

* Generate random **Initialization Vectors (IVs)** for AES-CBC encryption
* Ensure semantic security of encrypted ESP payloads

---

##### 🧠 Why These Libraries Were Chosen

* **Scapy** enables low-level packet control not possible with standard socket APIs
* **PyCryptodome** provides reliable and standardized cryptographic primitives
* Together, they allow a realistic, protocol-compliant ESP implementation
* The combination makes it possible to study covert channels without modifying kernel IPsec stacks

---


#### 5.3 Sender (`sender.py`)

##### Purpose

The sender is responsible for constructing and transmitting **ESP-encapsulated IPv6 packets**.
It supports two operational modes:

* **Baseline mode:** Sends ESP packets without any covert data
* **Covert mode:** Embeds covert data inside the ESP padding field

This allows a direct comparison between normal ESP traffic and covert-channel-enabled traffic.

---

##### High-Level Operation

For each packet transmission, the sender performs the following steps:

1. Constructs an **inner IPv6 + UDP packet**
2. Encapsulates the inner packet within an **ESP payload**
3. Computes ESP padding required for AES block alignment
4. Optionally embeds covert data into the ESP padding
5. Encrypts the ESP payload using **AES-CBC**
6. Computes an integrity check using **HMAC-SHA1**
7. Wraps the ESP payload inside an **outer IPv6 packet**
8. Sends the packet at Layer 2 using Scapy

All ESP packets use a fixed **Security Parameter Index (SPI)** and a monotonically increasing **sequence number**.

---

##### Sender Modes

###### Baseline Mode

* No covert data is embedded
* ESP padding contains only zero bytes
* Used as a reference to measure normal ESP behavior and sender processing time

Executed as:

```bash
sudo python3 sender.py --baseline
```

---

###### Covert Mode

* Random-length covert data is embedded inside ESP padding
* Covert data is transmitted only if sufficient padding space is available
* Packets that cannot safely carry covert data are skipped

Executed as:

```bash
sudo python3 sender.py --covert
```

---

##### Measurements Performed

For each successfully transmitted packet, the sender records:

* Sequence number
* Covert data length
* ESP padding length
* Total ESP packet size


---

#### 5.4 Receiver (`receiver.py`)

##### Purpose

The receiver listens for ESP packets sent by the sender and is responsible for **decrypting, verifying, and analyzing** them.
It extracts any embedded covert data and logs experimental results for later analysis.

---

##### High-Level Operation

For each received packet, the receiver performs the following steps:

1. Sniffs packets on the network interface in promiscuous mode
2. Extracts the ESP payload from the outer IPv6 packet
3. Verifies packet integrity using **HMAC-SHA1**
4. Decrypts the ESP payload using **AES-CBC**
5. Enforces **anti-replay protection** using sequence numbers
6. Parses the ESP plaintext to:

   * Recover padding information
   * Extract embedded covert data
7. Logs results for offline analysis

Packets failing integrity verification or replay checks are discarded.

---

##### Receiver Logging

The receiver records experimental metrics in the following files:

* `capacity_results.txt` — covert data length per packet
* `padlen_results.txt` — ESP padding length per packet

These logs are used to analyze:

* Covert channel capacity
* Padding utilization
* Distribution of covert payload sizes

---

#### 5.5 Baseline vs Covert Behavior

##### Baseline Mode Observations

* ESP packets contain no covert data
* Padding length remains constant across packets
* Receiver successfully decrypts packets without extracting covert bytes
* Serves as a correctness and performance reference

---

##### Covert Mode Observations

* Covert data is successfully extracted from ESP padding
* Padding length remains protocol-compliant
* Some packets intentionally skip covert transmission due to insufficient padding
* Receiver reconstructs covert data without affecting ESP integrity

---

#### 5.6 Outcome

The sender–receiver system demonstrates that:

* ESP padding can be exploited to carry covert information
* Cryptographic integrity and replay protection remain intact
* Covert communication is possible without modifying ESP headers
* Baseline comparison is essential for validating covert-channel behavior


---

#### 5.7 Sample Output and Observations

This section presents representative output from the sender and receiver to illustrate the behavior of the system in **baseline** and **covert** modes.

---

##### Sender Output (Baseline Mode)

Example output from the sender running in baseline mode:

```
[+] Sent ESP seq=3, payload_len=1, covert_len=0, pad_len=13, esp_len=124
[+] Sent ESP seq=3, covert_len=0, pad_len=13, sender_time=885.42 us, esp_len=124
```

**Explanation:**

* `covert_len=0` indicates no covert data is embedded
* `pad_len=13` shows a constant ESP padding length
* `esp_len=124` confirms uniform ESP packet size
* `sender_time` reports sender-side processing time in microseconds

This output establishes the **baseline behavior** of ESP packets without covert communication.

---

##### Receiver Output (Baseline Mode)

Example receiver output corresponding to baseline packets:

```
ESP SPI=0x100 SEQ=3 NEXT_HDR=17 PAD_LEN=13
Covert bytes: b''
```

**Explanation:**

* Packets are successfully decrypted and verified
* Padding is present but contains no covert data
* Confirms correct ESP construction and decryption

---

##### Sender Output (Covert Mode)

Example output from the sender running in covert mode:

```
[+] Sent ESP seq=4, payload_len=1, covert_len=9, pad_len=13, esp_len=124
[+] Sent ESP seq=4, covert_len=9, pad_len=13, sender_time=1509.43 us, esp_len=124
```

Occasionally, packets may be skipped:

```
[!] Can't send covert data, pad_len=13, covert_len=14 -> not enough space
[!] Packet seq=2: Covert data not sent
```

**Explanation:**

* `covert_len > 0` confirms covert data embedding
* Packets are skipped when ESP padding space is insufficient
* Ensures protocol-compliant packet construction
* Demonstrates dynamic covert payload handling

---

##### Receiver Output (Covert Mode)

Example receiver output in covert mode:

```
ESP SPI=0x100 SEQ=4 NEXT_HDR=17 PAD_LEN=13
Covert bytes: b'IIIIIIIII'
```

**Explanation:**

* Receiver successfully extracts covert data from ESP padding
* Padding length remains unchanged
* Covert data is invisible at the IP/UDP layer

---

##### Key Observations

* ESP packets are successfully transmitted and decrypted in both modes
* Baseline mode confirms correctness and stability
* Covert mode demonstrates hidden data transmission without protocol violations
* ESP padding provides a viable covert communication channel
* Anti-replay and integrity checks remain effective

---
