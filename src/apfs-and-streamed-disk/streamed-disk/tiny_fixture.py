"""In-memory test OCI. ASIF fixture/Apple LZ4 builder adapted with attribution
from ../full-disk/test_converter.py fixture() and apple_stream(), read-only.
No macOS data; independent explicit expected RAW bytes, including stale sectors.
"""
import json
import struct
import lz4.block
from frozen import oci

CS, BS = 32768, 512


def fixture():
    raw = bytearray(9 * CS + 3 * BS)
    struct.pack_into(">4sIIIQQ16sQQIHHQ16sIII", raw, 0,
                     b"shdw", 1, 512, 0, 512, 1024, bytes(range(16)),
                     (5 * CS + 3 * BS) // BS, 2 * CS * 2048 // BS,
                     CS, BS, 0, 0, bytes(16), 0, 0, 0)
    struct.pack_into(">QQQ", raw, 512, 3, 1, 0)
    struct.pack_into(">QQQ", raw, 1024, 9, 2, 0)
    struct.pack_into(">Q", raw, CS, (1 << 62) | 6)
    entries = [(1 << 62) | 7, 0, (3 << 62) | 5, 2 << 62,
               (1 << 62) | 6, (3 << 62) | 9]
    for v, value in enumerate(entries):
        struct.pack_into(">Q", raw, 2 * CS + v * 8, value)
    struct.pack_into(">Q", raw, 2 * CS + 2048 * 8, 3)
    for v, states in [(2, [1, 0, 2, 1, 1]), (5, [1, 0, 1, 3])]:
        for sector, state in enumerate(states):
            at = v * (CS // BS) + sector
            raw[3 * CS + at // 4] |= state << (2 * (at % 4))
    raw[5 * CS:6 * CS] = b"X" * CS
    raw[6 * CS:7 * CS] = b"B" * CS
    raw[7 * CS:8 * CS] = b"A" * CS
    raw[9 * CS:] = b"T" * (3 * BS)
    expected = bytearray(5 * CS + 3 * BS)
    expected[:CS] = b"A" * CS
    expected[2 * CS:2 * CS + BS] = b"X" * BS
    expected[2 * CS + 3 * BS:2 * CS + 5 * BS] = b"X" * (2 * BS)
    expected[4 * CS:5 * CS] = b"B" * CS
    expected[5 * CS:5 * CS + BS] = b"T" * BS
    expected[5 * CS + 2 * BS:] = b"T" * BS
    return bytes(raw), bytes(expected)


def apple_stream(data):
    out, previous = bytearray(), b""
    for start in range(0, len(data), 4096):
        block = data[start:start + 4096]
        if start == 0:
            out += b"bv4-" + struct.pack("<I", len(block)) + block
        else:
            packed = lz4.block.compress(block, store_size=False, dict=previous)
            out += b"bv41" + struct.pack("<II", len(block), len(packed)) + packed
        previous = block
    return bytes(out + b"bv4$")


def package(directory):
    raw, expected = fixture()
    config = b'{"diskFormat":"asif","os":"darwin","arch":"arm64"}'
    layers = [{"mediaType": oci.CONFIG_MEDIA, "size": len(config), "digest": oci.sha256(config)}]
    blobs = {}
    for start in range(0, len(raw), 65537):
        unpacked = raw[start:start + 65537]
        packed = apple_stream(unpacked)
        digest = oci.sha256(packed)
        blobs[digest[7:]] = packed
        layers.append({"mediaType": oci.DISK_MEDIA, "size": len(packed), "digest": digest,
                       "annotations": {oci.SIZE_ANNOTATION: str(len(unpacked)),
                                       oci.HASH_ANNOTATION: oci.sha256(unpacked)}})
    manifest = json.dumps({"schemaVersion": 2, "mediaType": oci.MANIFEST_MEDIA,
                           "layers": layers}, separators=(",", ":")).encode()
    (directory / "manifest.json").write_bytes(manifest)
    (directory / "config.json").write_bytes(config)
    digest = oci.sha256(manifest)
    pins = oci.load_pins(directory / "manifest.json", directory / "config.json", digest)
    return pins, blobs, expected
