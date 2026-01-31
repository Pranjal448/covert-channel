#!/bin/bash
set -e

BASELINE_PCAP="baseline_traffic.pcap"
COVERT_PCAP="covert_traffic.pcap"

echo ""
echo "=============================="
echo "  ESP Covert Channel Entropy Test"
echo "=============================="
echo ""

echo "[1/6] Capturing 10,000 ESP packets for BASELINE..."
#sudo tcpdump -i enp1s0 -w baseline_traffic.pcap -c 1000 "ip6 and proto 50"

echo "[2/6] Capturing 10,000 ESP packets for COVERT..."
#sudo tcpdump -i enp1s0 -w covert_traffic.pcap -c 1000 "ip6 and proto 50"

echo "[3/6] Dumping hex from baseline pcap..."
tshark -r $BASELINE_PCAP -Y "ipv6.nxt==50" -x > baseline_dump.txt

echo "[3/6] Dumping hex from covert pcap..."
tshark -r $COVERT_PCAP   -Y "ipv6.nxt==50" -x > covert_dump.txt

echo "[4/6] Extracting raw hex payload..."

# Baseline extractor
grep -A999 "0000" baseline_dump.txt \
| sed 's/^[0-9a-fA-F]*\s//' \
| grep -oE '([0-9a-fA-F]{2}\s+)+' \
| tr -d ' ' \
> baseline.hex

# Covert extractor
grep -A999 "0000" covert_dump.txt \
| sed 's/^[0-9a-fA-F]*\s//' \
| grep -oE '([0-9a-fA-F]{2}\s+)+' \
| tr -d ' ' \
> covert.hex

echo "[5/6] Converting hex \u2192 binary..."
xxd -r -p baseline.hex baseline.bin
xxd -r -p covert.hex covert.bin

echo "[6/6] Running ENTROPY analysis..."
echo "----- BASELINE ENTROPY -----" | tee baseline_entropy.log
ent baseline.bin | tee -a baseline_entropy.log

echo ""
echo "----- COVERT ENTROPY -----" | tee covert_entropy.log
ent covert.bin | tee -a covert_entropy.log

echo ""
echo "DONE!"
echo "Results saved as:"
echo "  - baseline_entropy.log"
echo "  - covert_entropy.log"
echo ""
echo "Expected: Baseline entropy \u2248 Covert entropy (~7.0\u20137.99 bits/byte)"