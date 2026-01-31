#!/usr/bin/env python3
import struct
from scapy.all import Ether, IPv6, UDP, Raw, sendp
from Cryptodome.Cipher import AES
from Cryptodome.Hash import HMAC, SHA1
from Cryptodome.Random import get_random_bytes
import time

IFACE = "enp1s0"
OUT_SRC = "2001:db8:100::10"
OUT_DST = "2001:db8:100::20"


# === Inner packet (UDP) ===
INNER_SRC = "2001:db8:2::1"
INNER_DST = "2001:db8:2::2"
SRC_PORT = 4444
DST_PORT = 5555

# === Crypto keys ===
ENC_KEY = bytes.fromhex("0102030405060708090a0b0c0d0e0f10")
AUTH_KEY = bytes.fromhex("1112131415161718191a1b1c1d1e1f2021222324")

SPI = 0x100
SEQ_START = 1
BLOCKSIZE = 16
NEXT_HDR = 17  # UDP

# === Helper functions ===
def build_inner_bytes(payload: bytes):
    pkt = IPv6(src=INNER_SRC, dst=INNER_DST) / UDP(sport=SRC_PORT, dport=DST_PORT) / Raw(load=payload)
    return bytes(pkt)


def make_plaintext(inner_bytes: bytes, covert: bytes):
    """
    Build ESP plaintext with covert data hidden inside the ESP padding field.
    - Padding structure: [covert_len (1 byte)] + [covert data] + [zeros]
    - If no space (pad_len <= 1 or covert too long), covert data cannot be sent.
    """
    covert_len = len(covert)
    if covert_len > 14:
        raise ValueError("covert data too long (max 255 bytes)")

    # Base length: inner + PadLen + NextHdr
    base_len = len(inner_bytes) + 2  # +2 for PadLen + NextHdr

    # Compute minimal pad length to align to AES block size
    pad_len = (BLOCKSIZE - (base_len % BLOCKSIZE)) % BLOCKSIZE

    if pad_len == 0:
        if covert_len > 0:
            print("[!] Can't send covert data, no padding space (already aligned)")
            return None, 0
        pad_len = 0  # no padding needed

    # Check if covert data fits in available padding (pad_len - 1 bytes)
    if covert_len > (pad_len - 1):
        print(f"[!] Can't send covert data, pad_len={pad_len}, covert_len={covert_len} -> not enough space")
        return None, 0

    # Build padding: first byte = covert length, then covert data, then zeros
    padding = bytes([covert_len]) + covert + bytes([0] * (pad_len - 1 - covert_len))

    pad_len_byte = bytes([pad_len])
    next_hdr_byte = bytes([NEXT_HDR])

    # ESP plaintext layout: inner_bytes | padding | pad_len | next_hdr
    plaintext = inner_bytes + padding + pad_len_byte + next_hdr_byte
    return plaintext, pad_len



def esp_encrypt(spi, seq, plaintext, ENC_KEY, AUTH_KEY):
    """
    Encrypt ESP plaintext with AES-CBC and compute HMAC-SHA1 ICV.
    """
    iv = get_random_bytes(BLOCKSIZE)

    # AES PKCS#7 padding for block alignment
    pad_len = BLOCKSIZE - (len(plaintext) % BLOCKSIZE)
    if pad_len == 0:
        pad_len = BLOCKSIZE
    plaintext_padded = plaintext + bytes([pad_len] * pad_len)

    cipher = AES.new(ENC_KEY, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(plaintext_padded)

    # ESP header (SPI + Sequence)
    esp_hdr = struct.pack("!I", spi) + struct.pack("!I", seq)

    # HMAC-SHA1 Integrity Check Value
    h = HMAC.new(AUTH_KEY, digestmod=SHA1)
    h.update(esp_hdr + iv + ciphertext)
    icv = h.digest()

    return esp_hdr + iv + ciphertext + icv


# === ESP sender ===
def send_esp(payload: bytes, covert: bytes, seq: int):

    # Start timing exactly when CPU work begins
    t_start = time.perf_counter()

    inner = build_inner_bytes(payload)
    plaintext, pad_len = make_plaintext(inner, covert)
    if plaintext is None:
        # Covert data could not be sent
        print(f"[!] Packet seq={seq}: Covert data not sent")
        return

    try:
        esp_bytes = esp_encrypt(SPI, seq, plaintext, ENC_KEY, AUTH_KEY)
        
        # End timing BEFORE sending the packet over the network
        t_end = time.perf_counter()
        elapsed_us = (t_end - t_start) * 1_000_000  # �s
        
        outer_pkt = (
            Ether(dst="ff:ff:ff:ff:ff:ff")
            / IPv6(src=OUT_SRC, dst=OUT_DST, nh=50)
            / Raw(load=esp_bytes)
        )
        
        with open("sent_packets.txt", "a") as f:
            f.write(outer_pkt.build().hex() + "\n")

        
        sendp(outer_pkt, iface=IFACE, verbose=False)
        print(
            f"[+] Sent ESP seq={seq}, payload_len={len(payload)}, covert_len={len(covert)}, "
            f"pad_len={pad_len}, esp_len={len(esp_bytes)}"
        )

        #\u2605\u2605 NEW: print sender processing time \u2605\u2605
        print(
            f"[+] Sent ESP seq={seq}, covert_len={len(covert)}, pad_len={pad_len}, "
            f"sender_time={elapsed_us:.2f} us, esp_len={len(esp_bytes)}"
        )

        # \u2605\u2605 NEW: save to timing_results.txt \u2605\u2605
        with open("timing_results.txt", "a") as f:
            f.write(f"{len(covert)},{elapsed_us:.2f}\n")


    except Exception as e:
        print(f"[!] Failed to send ESP seq={seq}: {e}")


# === Main ===
# if __name__ == "__main__":
#     seq = SEQ_START
#     for msg, covert in [(b"A"*16, b"L")]:
#         send_esp(msg, covert, seq)
#         seq += 1

import sys

import random


if __name__ == "__main__":
    seq = SEQ_START
    payload = b"A"

    mode = "baseline"
    if len(sys.argv) > 1 and sys.argv[1] == "--covert":
        mode = "covert"

    print(f"\n=== Sender Running in {mode.upper()} mode ===\n")

    if mode == "baseline":
        # covert_len = 0 (no covert data)
        for _ in range(10000):  # send many packets
            covert = b""
            send_esp(payload, covert, seq)
            seq += 1

    elif mode == "covert":
        # covert_len = 1 to 14
        for _ in range(10000):
            covert_len = random.randint(1, 14)   # always fits in padding
            covert = bytes([random.randint(0,255)]) * covert_len
            send_esp(payload, covert, seq)
            seq += 1
