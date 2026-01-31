#!/usr/bin/env python3
import struct
from scapy.all import sniff, Raw, IPv6
from Cryptodome.Cipher import AES
from Cryptodome.Hash import HMAC, SHA1
import time


IFACE = "enp1s0"
ENC_KEY = bytes.fromhex("0102030405060708090a0b0c0d0e0f10")
AUTH_KEY = bytes.fromhex("1112131415161718191a1b1c1d1e1f2021222324")
SPI_EXPECT = 0x100
BLOCKSIZE = 16

# Anti-replay state
LAST_SEQ = 0

def unpad_aes(padded: bytes):
    pad_len = padded[-1]
    if pad_len < 1 or pad_len > BLOCKSIZE:
        return padded
    return padded[:-pad_len]

def parse_plaintext(plaintext: bytes):
    if len(plaintext) < 2:
        return b"", b"", 0, 0
    pad_len = plaintext[-2]
    next_hdr = plaintext[-1]
    inner_and_pad = plaintext[:-2]
    padding = inner_and_pad[-pad_len:] if pad_len > 0 else b""
    inner_bytes = inner_and_pad[:-pad_len] if pad_len > 0 else inner_and_pad
    covert = b""
    if len(padding) >= 1:
        covert_len = padding[0]
        covert = padding[1:1+covert_len]
    return inner_bytes, covert, pad_len, next_hdr

def esp_decrypt_verify(esp_bytes, ENC_KEY, AUTH_KEY):
    """
    Verify ICV and decrypt. Returns (spi, seq, plaintext).
    Raises ValueError on any failure.
    """
    if len(esp_bytes) < 4+4+BLOCKSIZE+20:
        raise ValueError("ESP too short")

    spi = struct.unpack("!I", esp_bytes[0:4])[0]
    seq = struct.unpack("!I", esp_bytes[4:8])[0]
    iv = esp_bytes[8:8+BLOCKSIZE]
    icv = esp_bytes[-20:]
    ciphertext = esp_bytes[8+BLOCKSIZE:-20]

    if spi != SPI_EXPECT:
        raise ValueError(f"Unexpected SPI {spi}")

    # Verify ICV (HMAC-SHA1)
    h = HMAC.new(AUTH_KEY, digestmod=SHA1)
    h.update(esp_bytes[0:8] + iv + ciphertext)
    try:
        h.verify(icv)
    except Exception:
        raise ValueError("ICV verification failed")

    # Decrypt AES-CBC
    cipher = AES.new(ENC_KEY, AES.MODE_CBC, iv)
    plaintext_padded = cipher.decrypt(ciphertext)
    plaintext = unpad_aes(plaintext_padded)
    return spi, seq, plaintext

def handle_pkt(pkt):
    global LAST_SEQ

    if not pkt.haslayer(IPv6):
        return

    # extract ESP raw bytes (payload of outer IPv6)
    esp_bytes = bytes(pkt[IPv6].payload)

    try:
        spi, seq, plaintext = esp_decrypt_verify(esp_bytes, ENC_KEY, AUTH_KEY)
    except Exception as e:
        print("Packet dropped:", e)
        return

    # Anti-replay: only accept strictly increasing sequence numbers
    if seq <= LAST_SEQ:
        print(f"Replay detected: seq={seq} <= last_seq={LAST_SEQ} -> dropped")
        return
    LAST_SEQ = seq

    # parse inner & covert
    inner_bytes, covert, pad_len, next_hdr = parse_plaintext(plaintext)

    print(f"\nESP SPI={hex(spi)} SEQ={seq} NEXT_HDR={next_hdr} PAD_LEN={pad_len}")
    print("Covert bytes:", covert)
    # print("Inner bytes first 50:", inner_bytes[:50])

    # Log covert length for capacity analysis
    covert_len = len(covert)
    with open("capacity_results.txt", "a") as f:
        f.write(f"{seq},{covert_len}\n")
    
    # Inside handle_pkt
    pad_len = pad_len  # already parsed
    with open("padlen_results.txt", "a") as f:
        f.write(f"{seq},{pad_len}\n")


if __name__ == "__main__":
    print(f"Receiver sniffing on {IFACE} (ESP). Ctrl-C to stop.")
    sniff(iface=IFACE, prn=handle_pkt, store=False, promisc=True)

