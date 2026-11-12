"""Independent manufactured APFS objects; no guest bytes or network required.

Layout authority: Apple's APFS Reference, pp. 48, 127, 131-133, 150-153.
Fixture Fletcher and node/OMAP builders deliberately do not use reader encoders.
Run in the pinned image via apfs-headerless/run-tests.py.
"""
import hashlib
import struct
import unittest
from types import SimpleNamespace

from fs_explorer.errors import CorruptDataError, UnsupportedFormatError
from fs_explorer.io.cache import Cache
from fs_explorer.io.source import BytesRA
from fs_explorer.io.stats import Stats
from fs_explorer.filesystems.apfs import btree, container, fs

BS = 4096
ALG = {1: "sha256", 2: "sha512_256", 3: "sha384", 4: "sha512"}


def digest(data, algorithm=1):
    return hashlib.new(ALG[algorithm], data).digest()


def checksum(data):
    data = bytearray(data)
    first = second = 0
    for (word,) in struct.iter_unpack("<I", data[8:]):
        first = (first + word) % 0xffffffff
        second = (second + first) % 0xffffffff
    low = 0xffffffff - ((first + second) % 0xffffffff)
    high = 0xffffffff - ((first + low) % 0xffffffff)
    struct.pack_into("<Q", data, 0, (high << 32) | low)
    return bytes(data)


def object_block(kind, oid, size=BS):
    data = bytearray(size)
    struct.pack_into("<QQQII", data, 0, 0, oid, 7, kind, 0)
    return data


def node(entries, *, level=0, root=True, sealed=False, treeflags=None,
         fixed=None, size=BS, flags=None, oid=5):
    """Build ordinary or zero-header nodes at the documented unchanged offsets."""
    data = bytearray(size) if sealed else object_block(2 if root else 3, oid, size)
    if flags is None:
        flags = (1 if root else 0) | (2 if level == 0 else 0) | (0x18 if sealed else 0)
        if fixed:
            flags |= 4
    ent_size = 4 if fixed else 8
    tlen = ent_size * len(entries)
    struct.pack_into("<HHIHHHHHHHH", data, 32, flags, level, len(entries), 0, tlen, 0, 0, 0xffff, 0, 0xffff, 0)
    kstart = 56 + tlen
    vend = size - (40 if root else 0)
    ko = vo = 0
    for i, (key, val) in enumerate(entries):
        vo += len(val)
        data[kstart + ko:kstart + ko + len(key)] = key
        data[vend - vo:vend - vo + len(val)] = val
        if fixed:
            struct.pack_into("<HH", data, 56 + i * ent_size, ko, vo)
        else:
            struct.pack_into("<HHHH", data, 56 + i * ent_size, ko, len(key), vo, len(val))
        ko += len(key)
    if root:
        tf = (0x1c2 if sealed else 0) if treeflags is None else treeflags
        ks, vs = fixed or (0, 0)
        struct.pack_into("<IIIIIIQQ", data, size - 40, tf, size, ks, vs, 256, 256, len(entries), 2)
    return bytes(data) if sealed else checksum(data)


def fskey(oid, kind):
    return struct.pack("<Q", oid | kind << 60)


def records(filename_hashed=False):
    def inode(ino, mode):
        return struct.pack("<QQQQQQQiIIIIIHHQ", 2, ino, 1, 2, 3, 4, 0, 1, 0, 0, 0, 501, 20, mode, 0, 0)
    name = b"hello\0"
    if filename_hashed:
        dkey = fskey(2, 9) + struct.pack("<I", fs.name_hash("hello", True) << 10 | len(name)) + name
    else:
        dkey = fskey(2, 9) + struct.pack("<H", len(name)) + name
    return [(fskey(2, 3), inode(2, 0o40755)),
            (dkey, struct.pack("<QQH", 16, 0, 8)),
            (fskey(16, 3), inode(16, 0o100644))]


class Fixture:
    def __init__(self, sealed=True, algorithm=1, filename_hashed=False):
        self.algorithm = algorithm
        self.blocks = {}
        self.leaf = node(records(filename_hashed), root=False, sealed=sealed, oid=0x6000)
        childval = struct.pack("<Q", 0x6000)
        if sealed:
            # Nonzero padding is legal and must be preserved/ignored in comparison.
            childval += digest(self.leaf, algorithm).ljust(64, b"\xa5")
        self.root = node([(fskey(2, 3), childval)], level=1, sealed=sealed, oid=0x5000)
        self.blocks.update({5: self.root, 6: self.leaf, 7: node([], fixed=(16, 16), treeflags=0x10)})
        imeta = object_block(0x1e, 0x9000)
        struct.pack_into("<IIIIQ", imeta, 32, 2, 0, algorithm, 128, 0)
        imeta[128:128 + len(digest(self.root, algorithm))] = digest(self.root, algorithm)
        self.blocks[4] = checksum(imeta)
        self.mappings = {0x5000: (8 if sealed else 0, BS, 5),
                         0x6000: (8 if sealed else 0, BS, 6), 0x9000: (0, BS, 4)}
        self.vsb = object_block(0xd, 100)
        self.vsb[32:36] = b"APSB"
        struct.pack_into("<Q", self.vsb, 0x38, (0x20 if sealed else 0) | (1 if filename_hashed else 0))
        struct.pack_into("<I", self.vsb, 0x74, 2)
        struct.pack_into("<QQ", self.vsb, 0x80, 1, 0x5000)
        struct.pack_into("<Q", self.vsb, 0x108, 1)
        struct.pack_into("<H", self.vsb, 0x3c4, 1)
        struct.pack_into("<QQ", self.vsb, 0x400, 0x9000 if sealed else 0, 7 if sealed else 0)

    def imeta(self, offset, fmt, value):
        data = bytearray(self.blocks[4])
        struct.pack_into(fmt, data, offset, value)
        self.blocks[4] = checksum(data)

    def reseal(self):
        data = bytearray(self.blocks[4])
        h = digest(self.blocks[5], self.algorithm)
        data[128:128 + len(h)] = h
        self.blocks[4] = checksum(data)

    def open(self):
        omap = object_block(0xb, 1)
        struct.pack_into("<IIIIQQQ", omap, 32, 0, 0, 0x40000002, 0, 2, 0, 0)
        self.blocks[1] = checksum(omap)
        entries = [(struct.pack("<QQ", oid, 7), struct.pack("<IIQ", *value))
                   for oid, value in sorted(self.mappings.items())]
        self.blocks[2] = node(entries, fixed=(16, 16), treeflags=0x10, oid=2)
        c = container.Container.__new__(container.Container)
        c.ra = BytesRA(b"".join(self.blocks.get(i, bytes(BS)) for i in range(12)))
        c.block_size, c.nblocks, c.xid = BS, 12, 7
        stats = Stats()
        c.ctx = SimpleNamespace(cache=Cache(stats=stats), stats=stats, backend="pure")
        c.token = c.ctx.cache.token()
        self.c = c
        return fs.APFSVolume(c, checksum(self.vsb))


class HeaderlessTests(unittest.TestCase):
    def test_normal_lookup_before_failure(self):
        volume = Fixture(sealed=False).open()
        self.assertEqual(volume.inode(2).mode, 0o40755)
        self.assertEqual(volume.lookup(volume.root(), "hello").inode, 16)

    def test_sealed_inode_and_directory_lookup(self):
        for alg in ALG:
            for filenames in (False, True):
                with self.subTest(algorithm=alg, filename_hash=filenames):
                    fixture = Fixture(algorithm=alg, filename_hashed=filenames)
                    volume = fixture.open()
                    self.assertEqual(volume.inode(2).mode, 0o40755)
                    self.assertEqual(volume.lookup(volume.root(), "hello").inode, 16)
                    self.assertEqual([n.name for n in volume.children(volume.root())], ["hello"])
                    self.assertIsNone(volume.lookup(volume.root(), "missing"))

    def test_normal_bad_checksum(self):
        f = Fixture(sealed=False)
        f.blocks[5] = f.blocks[5][:-1] + b"\xff"
        with self.assertRaisesRegex(CorruptDataError, "checksum"):
            f.open().inode(2)

    def test_zero_header_without_authorization(self):
        f = Fixture()
        struct.pack_into("<Q", f.vsb, 0x38, 0)
        with self.assertRaises(CorruptDataError):
            f.open().inode(2)

    def test_wrong_root_hash_before_records(self):
        f = Fixture()
        f.imeta(128, "<B", f.blocks[4][128] ^ 1)
        with self.assertRaisesRegex(CorruptDataError, "root.*hash|hash.*root"):
            f.open().tree

    def test_wrong_root_hash_on_cached_root(self):
        f = Fixture()
        v = f.open()
        root = v.tree.root
        with self.assertRaisesRegex(CorruptDataError, "root.*hash|hash.*root"):
            btree.BTree(root, v._fs_node, "cached", hash_type=1, root_hash=bytes(32))

    def test_single_node_sealed_tree(self):
        f = Fixture()
        f.blocks[5] = node(records(), sealed=True)
        f.reseal()
        v = f.open()
        self.assertEqual(v.inode(2).ino, 2)
        self.assertEqual(v.lookup(v.root(), "hello").inode, 16)

    def test_full_object_hash_includes_header_and_padding(self):
        f = Fixture()
        f.imeta(128, "<32s", digest(f.blocks[5][32:]))
        with self.assertRaisesRegex(CorruptDataError, "root.*hash|hash.*root"):
            f.open().tree
        # An otherwise unused byte in a child still changes its sealed digest.
        f = Fixture()
        raw = bytearray(f.blocks[6])
        raw[2048] ^= 1
        f.blocks[6] = bytes(raw)
        with self.assertRaisesRegex(CorruptDataError, "child.*hash|hash.*child"):
            f.open().inode(2)

    def test_wrong_child_hash(self):
        f = Fixture()
        f.blocks[6] = f.blocks[6][:-1] + b"\xff"
        with self.assertRaisesRegex(CorruptDataError, "child.*hash|hash.*child"):
            f.open().inode(2)

    def test_wrong_child_hash_on_cache_hit(self):
        f = Fixture()
        v = f.open()
        self.assertEqual(v.inode(2).ino, 2)
        # New verified root refers to the same already-cached child with a wrong digest.
        raw = bytearray(f.blocks[5])
        struct.pack_into("<Q", raw, BS - 40 - 72, 0x6000)
        raw[BS - 40 - 64] ^= 1
        context = btree.NodeFormat(noheader=True, hashed=True, root=True, tree_type=2)
        root = btree.BNode(bytes(raw), v._keyfn, None, "test", context=context)
        tree = btree.BTree(root, v._fs_node, "test", hash_type=1, root_hash=digest(raw))
        before = f.c.ctx.stats.cache_hits
        with self.assertRaisesRegex(CorruptDataError, "child.*hash|hash.*child"):
            tree.get((2, 3))
        self.assertGreater(f.c.ctx.stats.cache_hits, before)

    def test_invalid_integrity_metadata(self):
        cases = [(24, "<I", 3), (32, "<I", 0), (32, "<I", 3),
                 (36, "<I", 1), (36, "<I", 2), (40, "<I", 0), (40, "<I", 5),
                 (44, "<I", 48), (44, "<I", BS - 16), (48, "<Q", 1)]
        for off, fmt, value in cases:
            with self.subTest(offset=off, value=value):
                f = Fixture()
                f.imeta(off, fmt, value)
                with self.assertRaises((CorruptDataError, UnsupportedFormatError)):
                    f.open().tree

    def test_imeta_checksum_and_omap_required(self):
        for fault in ("checksum", "missing", "headerless", "size", "identity"):
            with self.subTest(fault=fault):
                f = Fixture()
                if fault == "checksum":
                    f.blocks[4] = f.blocks[4][:-1] + b"\xff"
                elif fault == "missing":
                    del f.mappings[0x9000]
                elif fault == "headerless":
                    f.mappings[0x9000] = (8, BS, 4)
                elif fault == "identity":
                    f.imeta(8, "<Q", 0x7777)
                else:
                    f.mappings[0x9000] = (0, BS - 1, 4)
                with self.assertRaises(CorruptDataError):
                    f.open().tree

    def test_integrity_version_one(self):
        f = Fixture()
        f.imeta(32, "<I", 1)
        self.assertEqual(f.open().inode(2).ino, 2)

    def test_headerless_structure(self):
        for off, fmt, value in [(0, "<Q", 1), (32, "<H", 0x9), (32, "<H", 0x11),
                                (32, "<H", 0x1b), (32, "<H", 0x8019), (34, "<H", 16),
                                (36, "<I", 500), (40, "<H", 4095),
                                (BS - 40, "<I", 0x1d2), (BS - 40, "<I", 0x142),
                                (BS - 36, "<I", 8192)]:
            with self.subTest(offset=off, value=value):
                f = Fixture()
                raw = bytearray(f.blocks[5])
                struct.pack_into(fmt, raw, off, value)
                f.blocks[5] = bytes(raw)
                f.reseal()
                with self.assertRaises(CorruptDataError):
                    f.open().tree

    def test_malformed_key_value_records(self):
        for off, value in [(56, 4090), (58, 0), (60, 4090), (62, 8), (62, 39), (62, 73)]:
            with self.subTest(offset=off, value=value):
                f = Fixture()
                raw = bytearray(f.blocks[5])
                struct.pack_into("<H", raw, off, value)
                f.blocks[5] = bytes(raw)
                f.reseal()
                with self.assertRaises(CorruptDataError):
                    f.open().inode(2)

    def test_mapped_size_and_address_bounds(self):
        for flags, size, addr in [(8, 0, 5), (8, 4095, 5), (8, 8192, 11), (8, BS, 12), (0, BS, 5), (0x28, BS, 5)]:
            with self.subTest(mapping=(flags, size, addr)):
                f = Fixture()
                f.mappings[0x5000] = (flags, size, addr)
                with self.assertRaises(CorruptDataError):
                    f.open().tree

    def test_virtual_child_mapping_required(self):
        f = Fixture()
        del f.mappings[0x6000]
        with self.assertRaisesRegex(CorruptDataError, "object map"):
            f.open().inode(2)

    def test_child_levels_root_flag_and_cycle(self):
        for kind in ("level", "root", "cycle"):
            with self.subTest(kind=kind):
                f = Fixture()
                if kind == "cycle":
                    f.mappings[0x6000] = (8, BS, 5)
                else:
                    raw = bytearray(f.blocks[6])
                    struct.pack_into("<HH", raw, 32, 0x19 if kind == "root" else 0x18, 1)
                    f.blocks[6] = bytes(raw)
                    root = bytearray(f.blocks[5])
                    root[BS - 40 - 64:BS - 40 - 32] = digest(raw)
                    f.blocks[5] = bytes(root)
                    f.reseal()
                with self.assertRaises(CorruptDataError):
                    f.open().inode(2)

    def test_cache_separates_format_key_size_oid_and_decryption(self):
        f = Fixture()
        v = f.open()
        self.assertEqual(v.inode(2).ino, 2)
        # Same address cached as authorized headerless must not bypass normal Fletcher.
        with self.assertRaisesRegex(CorruptDataError, "checksum"):
            f.c.load_node(5, v._keyfn, None, "ordinary")
        # Same ordinary object under a different parser must not reuse parsed keys.
        n = f.c.load_node(7, lambda k: bytes(k), (16, 16), "first")
        other = f.c.load_node(7, lambda k: tuple(k), (16, 16), "second")
        self.assertIsNot(n, other)
        with self.assertRaises(CorruptDataError):
            f.c.load_node(7, v._keyfn, None, "bad decrypt", decrypt=lambda data, _: bytes(len(data)))
        with self.assertRaises(CorruptDataError):
            f.c.load_node(7, v._keyfn, None, "bad size", size=1)

    def test_cache_context_identity(self):
        f = Fixture(sealed=False)
        v = f.open()
        keyfn = v._keyfn
        identity = lambda data, _: data
        first = f.c.load_node(5, keyfn, None, "cached", decrypt=identity, decrypt_context=b"key-one")
        self.assertIs(first, f.c.load_node(5, keyfn, None, "cached", decrypt=identity, decrypt_context=b"key-one"))
        others = [f.c.load_node(5, keyfn, None, "cached", oid=99, decrypt=identity, decrypt_context=b"key-one"),
                  f.c.load_node(5, keyfn, None, "cached", size=BS, decrypt=identity, decrypt_context=b"key-one"),
                  f.c.load_node(5, keyfn, None, "cached", decrypt=identity, decrypt_context=b"key-two")]
        self.assertTrue(all(other is not first for other in others))

    def test_short_nodes_unsorted_overlaps_and_missing_hash_context(self):
        for raw in (bytes(55), bytes(60), node([(b"b", b"v"), (b"a", b"v")])):
            with self.subTest(bytes=len(raw)):
                with self.assertRaises(CorruptDataError):
                    btree.BNode(raw, bytes, None, "malformed")
        f = Fixture()
        root = f.open().tree.root
        with self.assertRaises(CorruptDataError):
            btree.BTree(root, lambda *_: root, "missing context")
        with self.assertRaises(CorruptDataError):
            btree.BNode(f.blocks[5], bytes, None, "unauthorized")

    def test_contradictory_superblock_and_seal_fields(self):
        for offset, fmt, value in [(0x74, "<I", 3), (0x74, "<I", 0x80000002), (0x74, "<I", 0x08000002),
                                   (0x3c4, "<H", 0x40), (0x400, "<Q", 0), (0x408, "<Q", 0)]:
            with self.subTest(offset=offset, value=value):
                f = Fixture()
                struct.pack_into(fmt, f.vsb, offset, value)
                with self.assertRaises((CorruptDataError, UnsupportedFormatError)):
                    f.open().tree

    def test_deep_virtual_sealed_tree(self):
        f = Fixture()
        child = f.blocks[6]
        for level, oid, paddr, childoid in [(1, 0x8000, 8, 0x6000), (2, 0x9001, 9, 0x8000),
                                            (3, 0x5000, 5, 0x9001)]:
            child = node([(fskey(2, 3), struct.pack("<Q", childoid) + digest(child).ljust(64, b"\0"))],
                         root=level == 3, level=level, sealed=True)
            f.blocks[paddr] = child
            f.mappings[oid] = (8, BS, paddr)
        f.reseal()
        v = f.open()
        self.assertEqual(v.tree.root.level, 3)
        self.assertEqual(v.lookup(v.root(), "hello").inode, 16)

    def test_multiblock_mapped_root(self):
        f = Fixture()
        raw = node(records(), sealed=True, size=2 * BS)
        f.blocks[5], f.blocks[6] = raw[:BS], raw[BS:]
        f.mappings[0x5000] = (8, 2 * BS, 5)
        imeta = bytearray(f.blocks[4])
        imeta[128:160] = digest(raw)
        f.blocks[4] = checksum(imeta)
        self.assertEqual(f.open().inode(2).ino, 2)

    def test_iteration_hashes_next_subtree(self):
        for corrupt in (False, True):
            with self.subTest(corrupt=corrupt):
                f = Fixture()
                sibling = node([(fskey(32, 3), records()[0][1])], root=False, sealed=True)
                f.blocks[8] = sibling if not corrupt else sibling[:2048] + b"x" + sibling[2049:]
                f.mappings[0x8000] = (8, BS, 8)
                f.blocks[5] = node([(fskey(2, 3), struct.pack("<Q", 0x6000) + digest(f.blocks[6]).ljust(64, b"\0")),
                                    (fskey(32, 3), struct.pack("<Q", 0x8000) + digest(sibling).ljust(64, b"\0"))],
                                   level=1, sealed=True)
                f.reseal()
                v = f.open()
                if corrupt:
                    with self.assertRaisesRegex(CorruptDataError, "child.*hash|hash.*child"):
                        list(v.tree.iter_from((2, 3)))
                else:
                    self.assertEqual([key for key, _, _ in v.tree.iter_from((2, 3))][-1], (32, 3))

    def test_malformed_fs_names_and_record_values(self):
        for fault in ("name_length", "name_terminator", "inode", "directory"):
            with self.subTest(fault=fault):
                f = Fixture()
                recs = records()
                if fault == "inode":
                    recs[0] = (recs[0][0], b"short")
                elif fault == "directory":
                    recs[1] = (recs[1][0], b"short")
                elif fault == "name_length":
                    recs[1] = (fskey(2, 9) + struct.pack("<H", 50) + b"hello\0", recs[1][1])
                else:
                    recs[1] = (recs[1][0][:-1] + b"x", recs[1][1])
                f.blocks[6] = node(recs, sealed=True, root=False)
                f.blocks[5] = node([(fskey(2, 3), struct.pack("<Q", 0x6000) + digest(f.blocks[6]).ljust(64, b"\0"))],
                                   level=1, sealed=True)
                f.reseal()
                v = f.open()
                with self.assertRaises(CorruptDataError):
                    v.lookup(v.root(), "hello")

    def test_fixed_hashed_index_uses_full_72_byte_value(self):
        keyfn = lambda key: struct.unpack("<Q", key)[0]
        leafdata = node([(struct.pack("<Q", 1), b"contents")], sealed=True, root=False, fixed=(8, 8))
        leaf = btree.BNode(leafdata, keyfn, (8, 8), "leaf",
                          context=btree.NodeFormat(noheader=True, hashed=True, root=False, level=0))
        rootdata = node([(struct.pack("<Q", 1), struct.pack("<Q", 6) + digest(leafdata).ljust(64, b"z"))],
                        sealed=True, level=1, fixed=(8, 8))
        root = btree.BNode(rootdata, keyfn, (8, 8), "root",
                          context=btree.NodeFormat(noheader=True, hashed=True, root=True))
        tree = btree.BTree(root, lambda *_: leaf, "fixed sealed", hash_type=1, root_hash=digest(rootdata))
        self.assertEqual(bytes(tree.get(1)), b"contents")

    def test_sealed_file_info_keys_retain_address_suffix(self):
        # Apple's j_file_info_key_t has an additional uint64 info_and_lba.
        keys = [fskey(16, 13) + struct.pack("<Q", (1 << 56) | lba) for lba in (0, 1)]
        keyfn = fs.fs_keyfn(False)
        data = node([(key, b"hash-record") for key in keys], sealed=True)
        root = btree.BNode(data, keyfn, None, "file info",
                          context=btree.NodeFormat(noheader=True, hashed=True))
        self.assertEqual(root.keys, [keyfn(memoryview(key)) for key in keys])
        self.assertLess(root.keys[0], root.keys[1])

    def test_compact_hash_values_and_preserved_padding(self):
        for algorithm in ALG:
            maximum_padding = 64 - len(digest(b"", algorithm))
            for padding in sorted({0, min(1, maximum_padding), maximum_padding}):
                with self.subTest(algorithm=algorithm, padding=padding):
                    f = Fixture(algorithm=algorithm)
                    childval = struct.pack("<Q", 0x6000) + digest(f.blocks[6], algorithm) + b"\xa5" * padding
                    f.blocks[5] = node([(fskey(2, 3), childval)], level=1, sealed=True)
                    f.reseal()
                    self.assertEqual(f.open().inode(2).ino, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
