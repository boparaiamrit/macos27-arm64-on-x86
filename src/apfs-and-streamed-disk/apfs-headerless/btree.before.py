"""APFS objects and B-trees.

* :func:`fletcher64` / :func:`check_object` validate the checksum every APFS
  object starts with (``obj_phys_t.o_cksum``).
* :class:`BNode` parses a ``btree_node_phys_t``: table of contents (fixed or
  variable key/value locations), key area after the TOC, value area growing
  down from the end of the node (minus the ``btree_info_t`` footer of a root).
* :class:`BTree` searches and iterates a tree. Keys are turned into sortable
  Python tuples by a per-tree ``keyfn`` (the tree type's comparison function);
  index entries point to children by object id, resolved by a ``read_node``
  callback (physical address for omaps and fext trees, virtual via the volume
  omap for fs trees). APFS leaves have no sibling links, so forward iteration
  keeps a descent stack.

Parsed nodes are kept in ``ctx.cache`` (decrypted, checksum-verified).
"""

from __future__ import annotations

import bisect
import struct
from collections.abc import Callable, Iterator
from itertools import accumulate
from typing import Any

from ...errors import CorruptDataError
from ...io import cancel

OBJ = struct.Struct("<QQQII")        # o_cksum, o_oid, o_xid, o_type, o_subtype
OBJ_SIZE = 32

OBJECT_TYPE_MASK = 0x0000FFFF
OBJECT_TYPE_FLAGS_MASK = 0xFFFF0000
OBJ_VIRTUAL = 0x00000000
OBJ_EPHEMERAL = 0x80000000
OBJ_PHYSICAL = 0x40000000
OBJ_ENCRYPTED = 0x10000000

OBJECT_TYPE_NX_SUPERBLOCK = 0x01
OBJECT_TYPE_BTREE = 0x02
OBJECT_TYPE_BTREE_NODE = 0x03
OBJECT_TYPE_OMAP = 0x0B
OBJECT_TYPE_CHECKPOINT_MAP = 0x0C
OBJECT_TYPE_FS = 0x0D

# btn_flags
BTNODE_ROOT = 0x1
BTNODE_LEAF = 0x2
BTNODE_FIXED_KV_SIZE = 0x4
BTNODE_HASHED = 0x8
BTNODE_NOHEADER = 0x10

# bt_flags (btree_info_t)
BTREE_PHYSICAL = 0x10
BTREE_HASHED = 0x80

_NODE = struct.Struct("<HHIHHHHHHHH")   # flags, level, nkeys, table_space(off,len), free_space, key/val free lists
_INFO = struct.Struct("<IIIIIIQQ")      # bt_flags, node_size, key_size, val_size, longest_key, longest_val, nkeys, nnodes
INFO_SIZE = 40
_KV_FIXED = struct.Struct("<HH")
_KV_VAR = struct.Struct("<HHHH")
_U64 = struct.Struct("<Q")

MAX_DEPTH = 16
_M32 = 0xFFFFFFFF


def fletcher64(data: bytes | bytearray | memoryview) -> int:
    """APFS Fletcher-64 over ``data`` (the object bytes after the checksum field); the bundled
    fsx kernel when available, else :func:`fletcher64_pure`."""
    from ...codecs import native
    k = native.kernel("fsmeta")
    if k is not None:
        return int(k.fletcher64(data))
    return fletcher64_pure(data)


def fletcher64_pure(data: bytes | bytearray | memoryview) -> int:
    """:func:`fletcher64` in pure Python."""
    words = memoryview(data).cast("B")
    n = len(words) // 4
    w: tuple[int, ...] = struct.unpack_from(f"<{n}I", words)
    # sum1 = sum(w); sum2 = the sum of the running sums; the per-step modulo of the reference loop
    # does not change the residues.
    s1 = sum(w) % _M32
    s2: int = sum(accumulate(w)) % _M32
    c1 = _M32 - ((s1 + s2) % _M32)
    c2 = _M32 - ((s1 + c1) % _M32)
    return (c2 << 32) | c1


def checksum_ok(block: bytes | bytearray | memoryview) -> bool:
    if len(block) < OBJ_SIZE:
        return False
    stored: int = _U64.unpack_from(block, 0)[0]
    if stored == 0 or stored == 0xFFFFFFFFFFFFFFFF:
        return False
    from ...codecs import native
    k = native.kernel("fsmeta")
    if k is not None:
        return bool(k.fletcher64(block, 8) == stored)
    return fletcher64_pure(memoryview(block)[8:]) == stored


def check_object(block: bytes, what: str) -> tuple[int, int, int, int]:
    """Verify the checksum; return ``(oid, xid, type, subtype)``."""
    if not checksum_ok(block):
        raise CorruptDataError(f"apfs: checksum mismatch in {what}")
    _, oid, xid, otype, sub = OBJ.unpack_from(block, 0)
    return oid, xid, otype, sub


class BNode:
    """A parsed B-tree node. ``keys`` holds the sortable key tuples.

    ``keyfn(key_bytes)`` makes one key tuple. It may also carry a ``many(data, kstart, vend, locs,
    what)`` attribute that checks the locations and makes every key of a node in one call, with
    the same results and errors as the generic loop.
    """

    __slots__ = ("data", "flags", "level", "nkeys", "keys", "_locs", "_kstart", "_vend", "fixed", "cache_cost",
                 "info", "oid")

    def __init__(self, data: bytes, keyfn: Callable[[memoryview], Any], fixed: tuple[int, int] | None,
                 what: str, oid: int = 0) -> None:
        self.data = data
        self.oid = oid
        size = len(data)
        if size < OBJ_SIZE + _NODE.size:
            raise CorruptDataError(f"apfs: {what}: node too small")
        otype = OBJ.unpack_from(data, 0)[3] & OBJECT_TYPE_MASK
        if otype not in (OBJECT_TYPE_BTREE, OBJECT_TYPE_BTREE_NODE):
            raise CorruptDataError(f"apfs: {what}: not a B-tree node (type {otype:#x})")
        flags, level, nkeys, toff, tlen, *_ = _NODE.unpack_from(data, OBJ_SIZE)
        self.flags = flags
        self.level: int = level
        self.nkeys = nkeys
        is_root = bool(flags & BTNODE_ROOT)
        self.info: tuple[int, ...] | None = None
        vend = size
        if is_root:
            vend -= INFO_SIZE
            self.info = _INFO.unpack_from(data, size - INFO_SIZE)
        base = OBJ_SIZE + _NODE.size
        kstart = base + toff + tlen
        if kstart > vend or level >= MAX_DEPTH:
            raise CorruptDataError(f"apfs: {what}: invalid node header")
        self._kstart = kstart
        self._vend = vend
        fixedkv = bool(flags & BTNODE_FIXED_KV_SIZE)
        ent = _KV_FIXED.size if fixedkv else _KV_VAR.size
        if nkeys * ent > tlen:
            raise CorruptDataError(f"apfs: {what}: table of contents overflow")
        mv = memoryview(data)
        locs: list[tuple[int, int, int, int]] = []
        if fixedkv:
            if fixed is None:
                raise CorruptDataError(f"apfs: {what}: fixed-size node in a variable-size tree")
            ksz, vsz = fixed
            if level > 0:
                vsz = 8
            for i in range(nkeys):
                k, v = _KV_FIXED.unpack_from(data, base + toff + i * 4)
                locs.append((k, ksz, v, vsz))
        else:
            for i in range(nkeys):
                locs.append(_KV_VAR.unpack_from(data, base + toff + i * 8))
        many = getattr(keyfn, "many", None)
        if many is not None:
            keys = many(data, kstart, vend, locs, what)
        else:
            keys = []
            for ko, kl, vo, vl in locs:
                ka = kstart + ko
                if ka + kl > vend or (vo != 0xFFFF and (vo > vend - kstart or vo < vl)):
                    raise CorruptDataError(f"apfs: {what}: key/value outside the node")
                keys.append(keyfn(mv[ka:ka + kl]))
        self.keys = keys
        self._locs = locs
        self.fixed = fixedkv
        self.cache_cost = size + 200 * nkeys + 200

    @property
    def is_leaf(self) -> bool:
        return self.level == 0

    def key(self, i: int) -> memoryview:
        ko, kl, _, _ = self._locs[i]
        a = self._kstart + ko
        return memoryview(self.data)[a:a + kl]

    def val(self, i: int) -> memoryview | None:
        _, _, vo, vl = self._locs[i]
        if vo == 0xFFFF:
            return None
        a = self._vend - vo
        return memoryview(self.data)[a:a + vl]

    def child(self, i: int) -> int:
        v = self.val(i)
        if v is None or len(v) < 8:
            raise CorruptDataError("apfs: index entry without a child pointer")
        child: int = _U64.unpack_from(v, 0)[0]
        return child


class BTree:
    """Search and iterate one B-tree.

    ``read_node(oid) -> BNode`` loads (and caches) a node; the tree only knows
    the root oid, the key function and the fixed key/value sizes.
    """

    def __init__(self, root: BNode, read_node: Callable[[int, int], BNode], what: str) -> None:
        if not root.flags & BTNODE_ROOT or root.info is None:
            raise CorruptDataError(f"apfs: {what}: root node lacks the root flag")
        self.root = root
        self.read_node = read_node
        self.what = what
        self.info = root.info

    def _child(self, node: BNode, i: int) -> BNode:
        c = self.read_node(node.child(i), node.level - 1)
        if c.level != node.level - 1:
            raise CorruptDataError(f"apfs: {self.what}: child level {c.level} under level {node.level}")
        return c

    def lookup_le(self, key: Any) -> tuple[Any, memoryview, memoryview | None] | None:
        """The entry with the greatest key <= ``key``, or None."""
        node = self.root
        for _ in range(MAX_DEPTH + 1):
            i = bisect.bisect_right(node.keys, key) - 1
            if i < 0:
                return None
            if node.is_leaf:
                return node.keys[i], node.key(i), node.val(i)
            node = self._child(node, i)
        raise CorruptDataError(f"apfs: {self.what}: tree too deep")

    def get(self, key: Any) -> memoryview | None:
        """Value of the entry whose key equals ``key`` (None when absent)."""
        r = self.lookup_le(key)
        if r is None or r[0] != key:
            return None
        return r[2]

    def iter_from(self, key: Any) -> Iterator[tuple[Any, None, memoryview | None]]:
        """Yield ``(key_tuple, None, value)`` for every entry >= ``key``, in order (the key bytes
        are :meth:`BNode.key` of the leaf, which no caller needs while iterating)."""
        stack: list[tuple[BNode, int]] = []
        node = self.root
        for _ in range(MAX_DEPTH + 1):
            if node.is_leaf:
                i = bisect.bisect_left(node.keys, key)
                break
            i = max(0, bisect.bisect_right(node.keys, key) - 1)
            if node.nkeys == 0:
                return
            stack.append((node, i))
            node = self._child(node, i)
        else:
            raise CorruptDataError(f"apfs: {self.what}: tree too deep")
        while True:
            keys, locs, vend = node.keys, node._locs, node._vend
            mv = memoryview(node.data)
            for j in range(i, len(keys)):
                vo, vl = locs[j][2], locs[j][3]
                yield keys[j], None, (None if vo == 0xFFFF else mv[vend - vo:vend - vo + vl])
            cancel.check()
            # climb to the next subtree
            while stack:
                parent, pi = stack.pop()
                if pi + 1 < parent.nkeys:
                    stack.append((parent, pi + 1))
                    node = self._child(parent, pi + 1)
                    while not node.is_leaf:
                        if node.nkeys == 0:
                            raise CorruptDataError(f"apfs: {self.what}: empty index node")
                        stack.append((node, 0))
                        node = self._child(node, 0)
                    i = 0
                    break
            else:
                return
