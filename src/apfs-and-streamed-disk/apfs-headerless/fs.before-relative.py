"""APFS volume: volume superblock, volume object map, fs tree records.

Records used (``j_key_t.obj_id_and_type``: low 60 bits object id, high 4 type):

* ``J_INODE`` (3): mode, owner, times (ns since the epoch), BSD flags, xfields
  (``INO_EXT_TYPE_DSTREAM`` for the size, ``INO_EXT_TYPE_RDEV``...).
* ``J_DREC`` (9): directory entries under the parent id. Normalization- and
  case-insensitive volumes use hashed keys (22-bit CRC-32C of the NFD,
  optionally case-folded, UTF-32 name), so a directory listing comes out in
  hash order, which is B-tree order.
* ``J_FILE_EXTENT`` (8): data extents keyed by the dstream id (the inode's
  ``private_id``); physical block 0 is a hole. On sealed volumes extents live
  in the separate ``fext`` tree.
* ``J_XATTR`` (4): extended attributes, embedded or in a dstream. Symlink
  targets are ``com.apple.fs.symlink``; compressed files (``UF_COMPRESSED``)
  keep a ``com.apple.decmpfs`` header plus, for the larger types, the payload
  in ``com.apple.ResourceFork``.
* ``J_SIBLING_LINK`` (5): hard links; a drec points directly at the shared
  inode, so hard links list as regular files with ``nlink > 1``.

System items: APFS keeps its private directory (id 3) outside the root, so
nothing needs hiding; ``.fseventsd`` and friends are ordinary entries.
Snapshots are not exposed (live tree only).
"""

from __future__ import annotations

import struct
import unicodedata
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from fs_explorer import modebits as _stat

from ...codecs.crc32c import crc32c_raw
from ...entry import EntryType, type_from_mode
from ...errors import CorruptDataError, FsExplorerError, NotAFileError, UnsupportedFormatError
from ...io import cancel
from ...io.blockmap import ChunkedRA, Extent, ExtentRA
from ...io.source import BytesRA, RandomAccess
from ...tree import DataSource, Node, Tree
from .btree import (OBJ_PHYSICAL, OBJ_NOHEADER, OBJ_ENCRYPTED, OBJECT_TYPE_MASK, BNode, BTree, NodeFormat,
                    check_object, hash_size)
from .container import APFS_INCOMPAT_SEALED_VOLUME, VolumeFacts
from .omap import OMAP_VAL_ENCRYPTED, OMAP_VAL_NOHEADER, OMap

if TYPE_CHECKING:
    from .container import Container

OBJ_ID_MASK = 0x0FFFFFFFFFFFFFFF
OBJ_TYPE_SHIFT = 60

J_SNAP_METADATA = 1
J_EXTENT = 2
J_INODE = 3
J_XATTR = 4
J_SIBLING_LINK = 5
J_DSTREAM_ID = 6
J_CRYPTO_STATE = 7
J_FILE_EXTENT = 8
J_DREC = 9
J_DIR_STATS = 10
J_SNAP_NAME = 11
J_SIBLING_MAP = 12
J_FILE_INFO = 13

ROOT_DIR_INO = 2
PRIV_DIR_INO = 3

J_DREC_LEN_MASK = 0x3FF
J_FILE_EXTENT_LEN_MASK = 0x00FFFFFFFFFFFFFF
FEXT_CRYPTO_ID_IS_TWEAK = 0x1

XATTR_DATA_STREAM = 0x1
XATTR_DATA_EMBEDDED = 0x2
XATTR_FILE_SYSTEM_OWNED = 0x4

INO_EXT_TYPE_NAME = 4
INO_EXT_TYPE_DSTREAM = 8
INO_EXT_TYPE_FS_UUID = 11
INO_EXT_TYPE_SPARSE_BYTES = 13
INO_EXT_TYPE_RDEV = 14

UF_COMPRESSED = 0x20

XATTR_DECMPFS = b"com.apple.decmpfs"
XATTR_RSRC = b"com.apple.ResourceFork"
XATTR_SYMLINK = b"com.apple.fs.symlink"
_HIDDEN_XATTRS = {XATTR_DECMPFS, XATTR_RSRC, XATTR_SYMLINK}

_U16 = struct.Struct("<H")
_U32 = struct.Struct("<I")
_U64 = struct.Struct("<Q")
_INODE = struct.Struct("<QQQQQQQiIIIIIHHQ")    # 92 bytes
_DREC_VAL = struct.Struct("<QQH")
_XATTR_VAL = struct.Struct("<HH")
_DSTREAM = struct.Struct("<QQQ")               # size, alloced_size, default_crypto_id
_EXTENT_VAL = struct.Struct("<QQQ")            # len_and_flags, phys_block_num, crypto_id
_FEXT_VAL = struct.Struct("<QQ")
_XF_HDR = struct.Struct("<HH")
_XF = struct.Struct("<BBH")

_DT_TYPES = {
    1: EntryType.FIFO, 2: EntryType.CHAR_DEVICE, 4: EntryType.DIR, 6: EntryType.BLOCK_DEVICE,
    8: EntryType.FILE, 10: EntryType.SYMLINK, 12: EntryType.SOCKET,
}

_CHUNK = 64 << 10


def fs_keyfn(hashed: bool) -> Callable[[memoryview], tuple[Any, ...]]:
    """Sortable key tuples for fs-tree keys (the ``CompareStdDirKey`` order)."""

    def name_end(data: bytes | memoryview, start: int, n: int, limit: int) -> int:
        end = start + n
        if n < 1 or end > limit or data[end - 1] != 0:
            raise CorruptDataError("apfs: malformed name length/terminator in fs-tree key")
        return end

    def key(mv: memoryview) -> tuple[Any, ...]:
        if len(mv) < 8:
            raise CorruptDataError("apfs: short fs-tree key")
        v = _U64.unpack_from(mv, 0)[0]
        oid = v & OBJ_ID_MASK
        t = v >> OBJ_TYPE_SHIFT
        if t == J_DREC:
            if hashed:
                if len(mv) < 12:
                    raise CorruptDataError("apfs: short directory record key")
                nlh = _U32.unpack_from(mv, 8)[0]
                n = nlh & J_DREC_LEN_MASK
                end = name_end(mv, 12, n, len(mv))
                return (oid, t, nlh >> 10, bytes(mv[12:end - 1]))
            if len(mv) < 10:
                raise CorruptDataError("apfs: short directory record key")
            n = _U16.unpack_from(mv, 8)[0]
            end = name_end(mv, 10, n, len(mv))
            return (oid, t, 0, bytes(mv[10:end - 1]))
        if t in (J_FILE_EXTENT, J_SIBLING_LINK, J_FILE_INFO):
            if len(mv) < 16:
                raise CorruptDataError("apfs: short fs-tree key")
            return (oid, t, _U64.unpack_from(mv, 8)[0])
        if t == J_XATTR or t == J_SNAP_NAME:
            if len(mv) < 10:
                raise CorruptDataError("apfs: short fs-tree key")
            n = _U16.unpack_from(mv, 8)[0]
            end = name_end(mv, 10, n, len(mv))
            return (oid, t, bytes(mv[10:end - 1]))
        return (oid, t)

    def many(data: bytes, kstart: int, vend: int, locs: list[tuple[int, int, int, int]],
             what: str) -> list[tuple[Any, ...]]:
        """The keys of a node: BNode's bounds check and ``key`` for each location, inlined."""
        out: list[tuple[Any, ...]] = []
        append = out.append
        u64, u32, u16 = _U64.unpack_from, _U32.unpack_from, _U16.unpack_from
        lim = vend - kstart
        for ko, kl, vo, vl in locs:
            ka = kstart + ko
            if ka + kl > vend or (vo != 0xFFFF and (vo > lim or vo < vl)):
                raise CorruptDataError(f"apfs: {what}: key/value outside the node")
            if kl < 8:
                raise CorruptDataError("apfs: short fs-tree key")
            v = u64(data, ka)[0]
            oid = v & OBJ_ID_MASK
            t = v >> OBJ_TYPE_SHIFT
            if t == J_DREC:
                if hashed:
                    if kl < 12:
                        raise CorruptDataError("apfs: short directory record key")
                    nlh = u32(data, ka + 8)[0]
                    end = name_end(data, ka + 12, nlh & J_DREC_LEN_MASK, ka + kl)
                    append((oid, t, nlh >> 10, data[ka + 12:end - 1]))
                else:
                    if kl < 10:
                        raise CorruptDataError("apfs: short directory record key")
                    end = name_end(data, ka + 10, u16(data, ka + 8)[0], ka + kl)
                    append((oid, t, 0, data[ka + 10:end - 1]))
            elif t in (J_FILE_EXTENT, J_SIBLING_LINK, J_FILE_INFO):
                if kl < 16:
                    raise CorruptDataError("apfs: short fs-tree key")
                append((oid, t, u64(data, ka + 8)[0]))
            elif t == J_XATTR or t == J_SNAP_NAME:
                if kl < 10:
                    raise CorruptDataError("apfs: short fs-tree key")
                end = name_end(data, ka + 10, u16(data, ka + 8)[0], ka + kl)
                append((oid, t, data[ka + 10:end - 1]))
            else:
                append((oid, t))
        return out

    key.many = many  # type: ignore[attr-defined]
    return key


def name_hash(name: str, case_insensitive: bool) -> int:
    """22-bit hash of a hashed ``J_DREC`` key: raw CRC-32C register (seed ~0, no final inversion, as in
    apfs-fuse and verified against macOS-made volumes) of the NFD (case-folded) UTF-32LE name."""
    s = unicodedata.normalize("NFD", name)
    if case_insensitive:
        s = unicodedata.normalize("NFD", s.casefold())
    return crc32c_raw(0xFFFFFFFF, s.encode("utf-32-le")) & 0x3FFFFF


def _fext_key(mv: memoryview) -> tuple[int, int]:
    if len(mv) < 16:
        raise CorruptDataError("apfs: short fext key")
    return struct.unpack_from("<QQ", mv, 0)


INODE_RUN_GAP = 64       # object ids this close are read in one walk when listing with stat


@dataclass(slots=True)
class Inode:
    ino: int
    parent: int
    private_id: int
    btime: int
    mtime: int
    ctime: int
    atime: int
    nlink: int
    bsd_flags: int
    uid: int
    gid: int
    mode: int
    size: int = 0
    alloced: int = 0
    crypto_id: int = 0
    rdev: int | None = None
    has_dstream: bool = False
    # data-stream extent records read so far (laddr, length, phys, crypto) and the extents built from them
    exts: tuple[list[tuple[int, int, int, int]], list[Extent]] | None = field(default=None, compare=False,
                                                                          repr=False)

    @property
    def compressed(self) -> bool:
        return bool(self.bsd_flags & UF_COMPRESSED)


def parse_inode(ino: int, mv: memoryview) -> Inode:
    end = len(mv)
    if end < _INODE.size:
        raise CorruptDataError(f"apfs: inode {ino}: short record")
    (parent, private_id, btime, mtime, ctime, atime, _iflags, nlink, _pclass, _gen, bsd_flags, uid, gid,
     mode, _pad, _usize) = _INODE.unpack_from(mv, 0)
    node = Inode(ino, parent, private_id, btime, mtime, ctime, atime, nlink, bsd_flags, uid, gid, mode)
    # extended fields (xf_blob_t): a count, then (type, flags, size) headers, then 8-aligned values;
    # only the data stream and the device number are kept
    off = _INODE.size
    if off + 4 > end:
        return node
    n = _XF_HDR.unpack_from(mv, off)[0]
    pos = off + 4 + 4 * n
    if pos > end:
        raise CorruptDataError("apfs: extended fields overflow the record")
    ds = rd = -1
    for t, _f, sz in _XF.iter_unpack(mv[off + 4:pos]):
        if pos + sz > end:
            raise CorruptDataError("apfs: extended field overflows the record")
        if t == INO_EXT_TYPE_DSTREAM:
            ds = pos if sz >= _DSTREAM.size else -1
        elif t == INO_EXT_TYPE_RDEV:
            rd = pos if sz >= 4 else -1
        pos += (sz + 7) & ~7
    if ds >= 0:
        node.size, node.alloced, node.crypto_id = _DSTREAM.unpack_from(mv, ds)
        node.has_dstream = True
    if rd >= 0:
        node.rdev = _U32.unpack_from(mv, rd)[0]
    return node


@dataclass(slots=True)
class _Ref:
    ino: int
    inode: Inode | None = None


class APFSVolume(Tree):
    format = "apfs"

    def __init__(self, c: Container, vsb: bytes, vek: bytes | None = None) -> None:
        self.c = c
        self.ctx = c.ctx
        self.facts = VolumeFacts(vsb)
        f = self.facts
        self.description = f'APFS volume "{f.name}"'
        self.xid = c.xid
        self.vek = vek
        self.hashed = bool(f.incompat & 0x9)
        self.case_insensitive = f.case_insensitive
        self.sealed = bool(f.incompat & APFS_INCOMPAT_SEALED_VOLUME)
        self._vsb = vsb
        self._keyfn = fs_keyfn(self.hashed)
        self._root_tree_type = _U32.unpack_from(vsb, 0x74)[0]
        self._physical = bool(self._root_tree_type & OBJ_PHYSICAL)
        self._seal_hash_type: int | None = None
        self._seal_root_hash: bytes | None = None
        self._node_size = 0
        self._tree: BTree | None = None
        self.fext: BTree | None = None
        if f.encrypted:
            self.description += " (encrypted)"
        self._root: Node | None = None

    @property
    def tree(self) -> BTree:
        """The fs tree, opened on first use (unlocking an encrypted volume then, so that probing
        and listing the container never need the password)."""
        if self._tree is None:
            c, f = self.c, self.facts
            if f.encrypted and self.vek is None:
                from .keybag import unlock_volume

                self.vek = unlock_volume(c, f)
            if f.encrypted:
                from ...crypto.backend import implementation

                self.ctx.note_backend("aes-xts", implementation("aes-xts", self.ctx.backend))
            self.omap = OMap(f.omap_oid, c.read_block, c.load_node, f'volume "{f.name}" object map')
            allowed_type = OBJECT_TYPE_MASK | OBJ_PHYSICAL | OBJ_NOHEADER | OBJ_ENCRYPTED
            if self._root_tree_type & OBJECT_TYPE_MASK != 2 or self._root_tree_type & ~allowed_type:
                raise CorruptDataError("apfs: unsupported fs-tree object type/storage")
            if self._root_tree_type & OBJ_NOHEADER and not self.sealed:
                raise CorruptDataError("apfs: headerless fs tree without a sealed volume")
            if self.sealed:
                if f.role_code != 1:
                    raise CorruptDataError("apfs: sealed volume is not a System volume")
                self._seal_hash_type, self._seal_root_hash = self._integrity_meta()
                fext_oid = _U64.unpack_from(self._vsb, 0x408)[0]
                if not fext_oid:
                    raise UnsupportedFormatError("apfs", "sealed volume without a file-extent tree")
                load: Callable[..., BNode] = lambda oid, level=-1: c.load_node(oid, _fext_key, (16, 16), "fext tree")  # noqa: E731
                self.fext = BTree(load(fext_oid), load, "fext tree")
            root = self._fs_node(f.root_tree_oid, -1)
            tree = BTree(root, self._fs_node, "fs tree", hash_type=self._seal_hash_type,
                         root_hash=self._seal_root_hash)
            self._node_size = tree.info[1]
            self._tree = tree
        return self._tree

    # ------------------------------------------------------------------ nodes

    def _integrity_meta(self) -> tuple[int, bytes]:
        """Resolve the virtual integrity OID through this volume's OMAP, then
        validate its ordinary Fletcher object before reading any root digest.

        Apple's packed v1 ends at byte 56; v2 adds nine reserved uint64s.
        This validates metadata consistency, not an externally trusted seal or
        file data hashes/signatures.
        """
        oid = _U64.unpack_from(self._vsb, 0x400)[0]
        if not oid:
            raise CorruptDataError("apfs: sealed volume without integrity metadata")
        m = self.omap.resolve(oid, self.xid, "integrity metadata")
        if m.flags & ~0x1f or m.flags & OMAP_VAL_NOHEADER or m.size <= 0 or m.size % self.c.block_size:
            raise CorruptDataError("apfs: invalid integrity metadata mapping")
        data = self.c.read_blocks(m.paddr, m.size // self.c.block_size)
        if m.flags & OMAP_VAL_ENCRYPTED:
            if self.vek is None:
                raise CorruptDataError("apfs: encrypted integrity metadata without key")
            data = self._decrypt_node(data, m.paddr)
        actual_oid, xid, kind, _ = check_object(data, "integrity metadata")
        if kind & ~OBJ_ENCRYPTED != 0x1e or actual_oid != oid or xid > self.xid:
            raise CorruptDataError("apfs: invalid integrity metadata object type/identity")
        if len(data) < 56:
            raise CorruptDataError("apfs: truncated integrity metadata")
        version, flags, algorithm, offset, broken_xid = struct.unpack_from("<IIIIQ", data, 32)
        if version not in (1, 2):
            raise UnsupportedFormatError("apfs", f"unsupported integrity metadata version {version}")
        if flags or broken_xid:
            raise CorruptDataError("apfs: broken or unsupported seal flags/transaction")
        minimum = 128 if version == 2 else 56
        size = hash_size(algorithm)
        if offset < minimum or offset + size > len(data):
            raise CorruptDataError("apfs: integrity root hash outside metadata object")
        return algorithm, data[offset:offset + size]

    def _decrypt_node(self, data: bytes, paddr: int) -> bytes:
        return self._xts(data, paddr * (self.c.block_size // 512))

    def _xts(self, data: bytes, sector: int) -> bytes:
        from ...crypto.backend import aes_xts_decrypt

        assert self.vek is not None
        out = aes_xts_decrypt(self.vek[:16], self.vek[16:32], data, sector, sector_size=512,
                              backend=self.ctx.backend)
        self.ctx.stats.bytes_decrypted += len(data)
        return out

    def _fs_node(self, oid: int, level: int) -> BNode:
        def context(mapping_flags: int = 0) -> NodeFormat:
            return NodeFormat(noheader=self.sealed, hashed=self.sealed, root=level == -1,
                              level=level, tree_type=self._root_tree_type, node_size=self._node_size,
                              mapping_flags=mapping_flags, hash_type=self._seal_hash_type)
        if self._physical:
            return self.c.load_node(oid, self._keyfn, None, "fs tree", oid=oid, context=context())
        m = self.omap.resolve(oid, self.xid, "fs tree")
        if m.flags & ~0x1f or m.size <= 0 or bool(m.flags & OMAP_VAL_NOHEADER) != self.sealed:
            raise CorruptDataError("apfs: fs-tree mapping contradicts sealed/headerless context")
        if m.flags & OMAP_VAL_ENCRYPTED and self.vek is None:
            raise CorruptDataError("apfs: encrypted fs-tree node without key")
        dec = self._decrypt_node if (m.flags & OMAP_VAL_ENCRYPTED and self.vek is not None) else None
        return self.c.load_node(m.paddr, self._keyfn, None, "fs tree", decrypt=dec, size=m.size, oid=oid,
                                context=context(m.flags), decrypt_context=self.vek)

    # ---------------------------------------------------------------- records

    def inode(self, ino: int) -> Inode:
        v = self.tree.get((ino, J_INODE))
        if v is None:
            raise CorruptDataError(f"apfs: inode {ino} not found")
        return parse_inode(ino, v)

    def _xattr_raw(self, ino: int, name: bytes) -> memoryview | None:
        return self.tree.get((ino, J_XATTR, name))

    def _xattr_value(self, ino: int, v: memoryview) -> DataSource:
        if len(v) < 4:
            raise CorruptDataError("apfs: short xattr record")
        flags, n = _XATTR_VAL.unpack_from(v, 0)
        body = v[4:4 + n]
        if flags & XATTR_DATA_EMBEDDED or not flags & XATTR_DATA_STREAM:
            return BytesRA(bytes(body))
        if len(body) < 8 + _DSTREAM.size:
            raise CorruptDataError("apfs: short xattr dstream")
        obj_id = _U64.unpack_from(body, 0)[0]
        size, _alloced, _crypto = _DSTREAM.unpack_from(body, 8)
        return self._dstream(obj_id, size)

    def xattr_bytes(self, ino: int, name: bytes, limit: int = 64 << 20) -> bytes | None:
        v = self._xattr_raw(ino, name)
        if v is None:
            return None
        ra = self._xattr_value(ino, v)
        assert isinstance(ra, RandomAccess)
        if ra.size > limit:
            raise CorruptDataError(f"apfs: xattr {name!r} too large ({ra.size} bytes)")
        return ra.read_exact(0, ra.size)

    def _dstream(self, obj_id: int, size: int) -> RandomAccess:
        """Data of a dstream (file data or xattr stream) as an ExtentRA with holes."""
        return ExtentRA(size, self._dstream_extents(obj_id, size)[1])

    def _file_extents(self, ino: Inode) -> tuple[list[tuple[int, int, int, int]], list[Extent]]:
        """:meth:`_dstream_extents` of a file's data stream, kept on the inode."""
        if ino.exts is None:
            ino.exts = self._dstream_extents(ino.private_id, ino.size)
        return ino.exts

    def _dstream_extents(self, obj_id: int, size: int) -> tuple[list[tuple[int, int, int, int]], list[Extent]]:
        """The extent records of a dstream, up to the first one at or past ``size``, and its extents."""
        self.tree   # noqa: B018 - opens the volume (and the fext tree of a sealed volume)
        c = self.c
        bs = c.block_size
        exts: list[Extent] = []
        if self.fext is not None:
            it: Iterator[tuple[int, int, int, int]] = (
                (k[1], ln & J_FILE_EXTENT_LEN_MASK, phys, 0)
                for k, _, v in _fext_iter(self.fext, obj_id)
                for ln, phys in [_FEXT_VAL.unpack_from(v, 0)])
        else:
            it = self._extent_iter(obj_id)
        recs: list[tuple[int, int, int, int]] = []
        for rec in it:
            recs.append(rec)
            laddr, length, phys, crypto = rec
            if laddr >= size:
                break
            cancel.check_bytes(4096)
            if phys == 0 or length == 0:
                continue
            nblk = (length + bs - 1) // bs
            if phys + nblk > c.nblocks:
                raise CorruptDataError(f"apfs: extent at block {phys} beyond the container")
            if self.vek is not None and crypto:
                ra: RandomAccess = self._crypt_extent(phys, nblk, crypto, length)
                exts.append(Extent(laddr, length, ra, 0))
            else:
                exts.append(Extent(laddr, length, c.ra, phys * bs))
        return recs, exts

    def _extent_iter(self, obj_id: int) -> Iterator[tuple[int, int, int, int]]:
        for k, _, v in self.tree.iter_from((obj_id, J_FILE_EXTENT)):
            if k[0] != obj_id or k[1] != J_FILE_EXTENT:
                return
            if v is None or len(v) < _EXTENT_VAL.size:
                raise CorruptDataError("apfs: short file extent record")
            lf, phys, crypto = _EXTENT_VAL.unpack_from(v, 0)
            if crypto and not (lf >> 56) & FEXT_CRYPTO_ID_IS_TWEAK:
                # crypto_id names a crypto-state record (the volume key on ONEKEY volumes):
                # the XTS tweak is then the physical address
                crypto = phys
            yield k[2], lf & J_FILE_EXTENT_LEN_MASK, phys, crypto

    def _crypt_extent(self, phys: int, nblk: int, crypto: int, length: int) -> RandomAccess:
        c = self.c
        bs = c.block_size
        chunk = max(bs, _CHUNK)
        per = chunk // bs
        spb = bs // 512

        def load(i: int) -> bytes:
            b0 = i * per
            n = min(per, nblk - b0)
            data = c.read_blocks(phys + b0, n)
            return self._xts(data, (crypto + b0) * spb)

        return ChunkedRA(length, load, chunk_size=chunk, cache=self.ctx.cache, stats=self.ctx.stats)

    # ------------------------------------------------------------------ nodes

    def _node(self, name: str, ref: _Ref) -> Node:
        n = Node(name, EntryType.FILE, ref=ref, inode=ref.ino)
        self._fill(n, ref.inode) if ref.inode is not None else None
        return n

    def _fill(self, n: Node, ino: Inode) -> None:
        n.type = type_from_mode(ino.mode, EntryType.OTHER)
        n.mode = ino.mode
        n.uid, n.gid = ino.uid, ino.gid
        n.mtime_ns, n.ctime_ns, n.atime_ns, n.btime_ns = ino.mtime, ino.ctime, ino.atime, ino.btime
        n.inode = ino.ino
        n.statted = True
        if n.type == EntryType.DIR:
            n.extra["nchildren"] = ino.nlink
            return
        n.nlink = ino.nlink
        if ino.rdev is not None:
            n.extra["rdev"] = ino.rdev
        if n.type == EntryType.SYMLINK:
            try:
                t = self.xattr_bytes(ino.ino, XATTR_SYMLINK, 1 << 20)
            except FsExplorerError as e:
                n.error, n.error_code = str(e), e.code
                t = None
            if t is not None:
                n.link_target = t.rstrip(b"\0").decode("utf-8", "surrogateescape")
                n.size = len(t.rstrip(b"\0"))
            return
        if n.type != EntryType.FILE:
            return
        n.size = ino.size
        n.stored_size = ino.alloced
        if ino.compressed:
            try:
                x = self.xattr_bytes(ino.ino, XATTR_DECMPFS, 1 << 26)
                if x is not None:
                    from ..decmpfs import parse_header

                    h = parse_header(x)
                    n.size = h.uncompressed_size
                    n.extra["compression"] = h.compression_type
                    rs = self._xattr_raw(ino.ino, XATTR_RSRC)
                    stored = len(x)
                    if rs is not None and len(rs) >= 4:
                        src = self._xattr_value(ino.ino, rs)
                        stored += src.size or 0
                    n.stored_size = stored
            except FsExplorerError as e:
                n.error, n.error_code = str(e), e.code

    def root(self) -> Node:
        if self._root is None:
            ref = _Ref(ROOT_DIR_INO, self.inode(ROOT_DIR_INO))
            self._root = self._node("", ref)
            self._root.type = EntryType.DIR
        return self._root

    def _drecs(self, parent: int) -> Iterator[tuple[str, int, int]]:
        for k, _, v in self.tree.iter_from((parent, J_DREC)):
            if k[0] != parent or k[1] != J_DREC:
                return
            if v is None or len(v) < _DREC_VAL.size:
                raise CorruptDataError("apfs: short directory record")
            file_id, _added, flags = _DREC_VAL.unpack_from(v, 0)
            yield k[3].decode("utf-8", "surrogateescape"), file_id, flags

    def children(self, node: Node, stat: bool = True) -> Iterator[Node]:
        ref: _Ref = node.ref
        if node.type != EntryType.DIR:
            return
        if not stat:
            for name, fid, flags in self._drecs(ref.ino):
                yield Node(name, _DT_TYPES.get(flags & 0xF, EntryType.OTHER), ref=_Ref(fid), inode=fid,
                           statted=False)
            return
        ents = list(self._drecs(ref.ino))
        inodes = self._inodes(sorted({e[1] for e in ents}))
        for name, fid, flags in ents:
            ino = inodes[fid]
            if isinstance(ino, str):
                yield Node(name, _DT_TYPES.get(flags & 0xF, EntryType.OTHER), ref=_Ref(fid), inode=fid, error=ino)
                continue
            yield self._node(name, _Ref(fid, ino))

    def _inodes(self, fids: list[int]) -> dict[int, Inode | str]:
        """Inode records of the sorted ``fids`` (an error message for each one missing or corrupt).

        Runs of close object ids are read in one walk over the tree's key order, rather than one
        root-to-leaf lookup each: a folder's children are usually created together."""
        out: dict[int, Inode | str] = {}
        i = 0
        while i < len(fids):
            j = i + 1
            while j < len(fids) and fids[j] - fids[j - 1] <= INODE_RUN_GAP:
                j += 1
            run, last = set(fids[i:j]), fids[j - 1]
            try:
                for n, (k, _, v) in enumerate(self.tree.iter_from((fids[i], J_INODE))):
                    if not n & 255:
                        cancel.check()
                    if k[0] > last:
                        break
                    if k[1] == J_INODE and k[0] in run:
                        try:
                            out[k[0]] = parse_inode(k[0], v) if v is not None else "apfs: empty inode record"
                        except CorruptDataError as e:
                            out[k[0]] = str(e)
            except CorruptDataError as e:
                for fid in run:
                    out.setdefault(fid, str(e))
            i = j
        for fid in fids:
            out.setdefault(fid, f"apfs: inode {fid} not found")
        return out

    def stat(self, node: Node) -> Node:
        ref: _Ref = node.ref
        if ref.inode is None:
            ref.inode = self.inode(ref.ino)
        self._fill(node, ref.inode)
        return node

    def _fold(self, s: str) -> str:
        s = unicodedata.normalize("NFD", s)
        if self.case_insensitive:
            s = unicodedata.normalize("NFD", s.casefold())
        return s

    def lookup(self, node: Node, name: str) -> Node | None:
        ref: _Ref = node.ref
        if node.type != EntryType.DIR:
            return None
        if not self.hashed:
            v = self.tree.get((ref.ino, J_DREC, 0, name.encode("utf-8", "surrogateescape")))
            if v is not None:
                if len(v) < _DREC_VAL.size:
                    raise CorruptDataError("apfs: short directory record")
                fid = _DREC_VAL.unpack_from(v, 0)[0]
                return self._stat_node(name, fid, _DREC_VAL.unpack_from(v, 0)[2])
            return super().lookup(node, name)
        h = name_hash(name, self.case_insensitive)
        want = self._fold(name)
        for k, _, v in self.tree.iter_from((ref.ino, J_DREC, h)):
            if k[0] != ref.ino or k[1] != J_DREC or k[2] != h:
                break
            cand = k[3].decode("utf-8", "surrogateescape")
            if self._fold(cand) == want:
                if v is None or len(v) < _DREC_VAL.size:
                    raise CorruptDataError("apfs: short directory record")
                fid, _added, flags = _DREC_VAL.unpack_from(v, 0)
                return self._stat_node(cand, fid, flags)
        if not name.isascii():
            # case folding tables may differ from Python's for exotic characters: scan the directory
            for name2, fid, flags in self._drecs(ref.ino):
                if self._fold(name2) == want:
                    return self._stat_node(name2, fid, flags)
        return None

    def _stat_node(self, name: str, fid: int, flags: int) -> Node:
        n = Node(name, _DT_TYPES.get(flags & 0xF, EntryType.OTHER), ref=_Ref(fid), inode=fid, statted=False)
        try:
            return self.stat(n)
        except CorruptDataError as e:
            n.error, n.error_code = str(e), e.code
            return n

    # ---------------------------------------------------------------- reading

    def _inode_of(self, node: Node) -> Inode:
        ref: _Ref = node.ref
        if ref.inode is None:
            ref.inode = self.inode(ref.ino)
        return ref.inode

    def storage_key(self, node: Node) -> tuple[int, ...] | None:
        """Physical block of the first extent of a file's data stream. Only for nodes
        whose inode is already loaded; the extent record usually shares the inode's
        (cached) leaf node, and reading the file needs it anyway."""
        ref = node.ref
        if not isinstance(ref, _Ref) or ref.inode is None:
            return None
        ino = ref.inode
        if not ino.has_dstream or ino.compressed or not _stat.S_ISREG(ino.mode):
            return None
        try:
            recs = self._file_extents(ino)[0]
        except FsExplorerError:
            recs = None
        try:
            if self.fext is not None:
                if recs is not None:
                    return (recs[0][2],) if recs else None
                for _k, _kb, v in _fext_iter(self.fext, ino.private_id):
                    return (_FEXT_VAL.unpack_from(v, 0)[1],)
                return None
            if recs is not None:
                return (recs[0][2],) if recs and recs[0][2] else None
            for _laddr, _length, phys, _crypto in self._extent_iter(ino.private_id):
                return (phys,) if phys else None
        except FsExplorerError:
            return None
        return None

    def open_file(self, node: Node) -> DataSource:
        ino = self._inode_of(node)
        if not _stat.S_ISREG(ino.mode):
            raise NotAFileError(node.name)
        if ino.compressed:
            x = self.xattr_bytes(ino.ino, XATTR_DECMPFS, 1 << 26)
            if x is not None:
                from ..decmpfs import open_compressed

                def rsrc() -> RandomAccess | None:
                    v = self._xattr_raw(ino.ino, XATTR_RSRC)
                    if v is None:
                        return None
                    src = self._xattr_value(ino.ino, v)
                    assert isinstance(src, RandomAccess)
                    return src

                return open_compressed(x, rsrc, self.ctx)
        if not ino.has_dstream:
            return BytesRA(b"")
        return ExtentRA(ino.size, self._file_extents(ino)[1])

    def readlink(self, node: Node) -> str | None:
        if node.link_target is None and not node.statted:
            self.stat(node)
        return node.link_target

    def volume_label(self) -> str | None:
        return self.facts.name or None

    def _iter_xattrs(self, ino: int) -> Iterator[tuple[bytes, memoryview]]:
        for k, _, v in self.tree.iter_from((ino, J_XATTR)):
            if k[0] != ino or k[1] != J_XATTR:
                return
            if v is None:
                continue
            yield k[2], v

    def xattrs(self, node: Node) -> dict[str, bytes]:
        ino = node.ref.ino
        out: dict[str, bytes] = {}
        for name, v in self._iter_xattrs(ino):
            if name in _HIDDEN_XATTRS or len(v) < 4 or _XATTR_VAL.unpack_from(v, 0)[0] & XATTR_FILE_SYSTEM_OWNED:
                continue
            ra = self._xattr_value(ino, v)
            assert isinstance(ra, RandomAccess)
            out[name.decode("utf-8", "surrogateescape")] = ra.read_exact(0, ra.size)
        return out

    def resource_fork(self, node: Node) -> DataSource | None:
        ino = self._inode_of(node)
        if ino.compressed or not _stat.S_ISREG(ino.mode):
            return None
        v = self._xattr_raw(ino.ino, XATTR_RSRC)
        if v is None:
            return None
        return self._xattr_value(ino.ino, v)


def _fext_iter(tree: BTree, obj_id: int) -> Iterator[tuple[Any, None, memoryview]]:
    for k, kb, v in tree.iter_from((obj_id, 0)):
        if k[0] != obj_id:
            return
        if v is None or len(v) < _FEXT_VAL.size:
            raise CorruptDataError("apfs: short fext record")
        yield k, kb, v
