#!/usr/bin/env python3
import struct, hashlib
from scapy.all import sniff, IPv6, Raw
from Cryptodome.Cipher import AES
from Cryptodome.Hash import HMAC, SHA1

# ===========================
# CONSTANTS
# ===========================
IFACE = "enp1s0"          # your NIC
SPI_EXPECT = 0x100
BLOCK = 16

ENC_KEY = bytes.fromhex("0102030405060708090a0b0c0d0e0f10")
AUTH_KEY = bytes.fromhex("1112131415161718191a1b1c1d1e1f2021222324")

# reassembly buffers / stats
chunks = {}
last_chunk = None
seen_packets = 0
valid_packets = 0


# ===========================
# HELPERS
# ===========================
def unpad(msg: bytes) -> bytes:
    pad = msg[-1]
    if 1 <= pad <= BLOCK:
        return msg[:-pad]
    return msg


def parse_esp(esp: bytes):
    """Verify HMAC + decrypt ESP, return (seq, plaintext)."""
    if len(esp) < 4 + 4 + BLOCK + 20:
        raise ValueError("ESP too short")

    spi = struct.unpack("!I", esp[:4])[0]
    seq = struct.unpack("!I", esp[4:8])[0]
    if spi != SPI_EXPECT:
        raise ValueError("Unexpected SPI")

    iv = esp[8:8 + BLOCK]
    icv = esp[-20:]
    ct = esp[8 + BLOCK:-20]

    h = HMAC.new(AUTH_KEY, digestmod=SHA1)
    h.update(esp[:8] + iv + ct)
    h.verify(icv)

    cipher = AES.new(ENC_KEY, AES.MODE_CBC, iv)
    pt = cipher.decrypt(ct)
    return seq, unpad(pt)


def extract_covert(pt: bytes):
    """Get covert bytes from ESP padding."""
    if len(pt) < 2:
        return None

    pad_len = pt[-2]
    inner_plus_pad = pt[:-2]
    if pad_len == 0 or pad_len > len(inner_plus_pad):
        return None

    padding = inner_plus_pad[-pad_len:]
    cov_len = padding[0]
    if cov_len == 0:
        return b""      # dummy packet, no covert
    return padding[1:1 + cov_len]


# ===========================
# PACKET HANDLER
# ===========================
def handle(pkt):
    global seen_packets, valid_packets, last_chunk, chunks

    if not pkt.haslayer(IPv6):
        return

    seen_packets += 1

    try:
        esp = bytes(pkt[IPv6].payload)
        seq, plaintext = parse_esp(esp)
        covert = extract_covert(plaintext)
    except Exception:
        # noise / invalid ESP
        return

    valid_packets += 1

    if covert is None or len(covert) < 3:
        # no covert / malformed
        return

    cid = (covert[0] << 8) | covert[1]
    last_flag = covert[2]
    data = covert[3:]

    chunks[cid] = data
    if last_flag == 1:
        last_chunk = cid

    print(f"[+] Chunk {cid}, size={len(data)}, last={last_flag}")


# ===========================
# REASSEMBLE & WRITE FILE
# ===========================
def write_output():
    if last_chunk is None:
        print("[!] No last chunk flag received \u2192 cannot rebuild file.")
        return

    print(f"[+] Reassembling chunks 0..{last_chunk}")
    out = b""
    for cid in range(last_chunk + 1):
        if cid not in chunks:
            print(f"[!] Missing chunk {cid} \u2192 file incomplete.")
            return
        out += chunks[cid]

    with open("received.bin", "wb") as f:
        f.write(out)

    print("[+] File written to received.bin")
    print("[+] SHA256:", hashlib.sha256(out).hexdigest())


# ===========================
# MAIN
# ===========================
if __name__ == "__main__":
    print(f"Receiver listening on {IFACE} (ESP)...")

    # Sniff EXACTLY 1000 ESP packets (your sender sends 1000)
    sniff(
        iface=IFACE,
        prn=handle,
        store=False,
        promisc=True,
        filter="ip6 and proto 50",
        count=1000
    )

    print("\n=== Sniffing finished ===")
    print("Packets seen: ", seen_packets)
    print("Valid ESP:    ", valid_packets)
    print("Chunks stored:", len(chunks))
    print("Last chunk:   ", last_chunk)

    write_output()
