"""APFS container: ``nx_superblock_t``, checkpoints, container object map, volumes.

The latest checkpoint is taken: every ``NXSB`` in the checkpoint descriptor
area is checked (Fletcher-64) and the one with the highest xid wins; block 0
is the fallback. Volumes are listed as ``v1..vN`` in ``nx_fs_oid`` array
order (unused slots skipped); each volume superblock is read once (one
block) for its name, role, UUID and flags. Opening a volume returns the
filesystem tree (:mod:`.fs`), unlocking native encryption first when needed.
"""

from __future__ import annotations

import struct
import uuid as _uuid
from collections.abc import Callable, Iterator
from typing import Any

from ...errors import CorruptDataError, FsExplorerError, UnsupportedFormatError
from ...io.source import RandomAccess
from ...tree import Context, Driver, Layer, ProbeHint, VolumeInfo, VolumeSet
from .btree import (
    OBJ,
    OBJECT_TYPE_MASK,
    OBJECT_TYPE_NX_SUPERBLOCK,
    BNode,
    check_object,
    checksum_ok,
)
from .omap import OMap

NX_MAGIC = b"NXSB"
APFS_MAGIC = b"APSB"
NX_MAX_FILE_SYSTEMS = 100

_NX = struct.Struct("<4sIQQQQ16sQQIIQQIIIIIIQQQII")
_NX_FS_OID = 0xB8
_NX_FLAGS = 0x4F0
_NX_KEYLOCKER = 0x510
_PRANGE = struct.Struct("<QQ")
_U64 = struct.Struct("<Q")

NX_CRYPTO_SW = 0x4

# apfs_superblock_t offsets
_APSB_INCOMPAT = 0x38
_APSB_ALLOC_COUNT = 0x58
_APSB_OMAP = 0x80
_APSB_ROOT_TREE = 0x88
_APSB_UUID = 0xF0
_APSB_FS_FLAGS = 0x108
_APSB_VOLNAME = 0x2C0
_APSB_ROLE = 0x3C4

APFS_FS_UNENCRYPTED = 0x1
APFS_FS_ONEKEY = 0x8
APFS_INCOMPAT_CASE_INSENSITIVE = 0x1
APFS_INCOMPAT_NORMALIZATION_INSENSITIVE = 0x8
APFS_INCOMPAT_SEALED_VOLUME = 0x20

_ROLES = {
    0x0: None, 0x1: "System", 0x2: "User", 0x4: "Recovery", 0x8: "VM", 0x10: "Preboot", 0x20: "Installer",
    0x40: "Data", 0x80: "Baseband", 0xC0: "Update", 0x100: "xART", 0x140: "Hardware", 0x180: "Backup",
    0x1C0: "Sidecar", 0x200: "Reserved-10", 0x240: "Enterprise", 0x280: "Reserved-12", 0x2C0: "Prelogin",
}


class Superblock:
    """The fields of ``nx_superblock_t`` the reader needs."""

    def __init__(self, blk: bytes) -> None:
        (magic, self.block_size, self.block_count, self.features, self.ro_features, self.incompat,
         uuid_b, self.next_oid, self.next_xid, self.xp_desc_blocks, self.xp_data_blocks, self.xp_desc_base,
         self.xp_data_base, _, _, _, _, _, _, self.spaceman_oid, self.omap_oid, self.reaper_oid, _,
         self.max_file_systems) = _NX.unpack_from(blk, 32)
        if magic != NX_MAGIC:
            raise CorruptDataError("apfs: bad container superblock magic")
        self.uuid = bytes(uuid_b)
        self.oid, self.xid = OBJ.unpack_from(blk, 0)[1:3]
        n = min(self.max_file_systems or NX_MAX_FILE_SYSTEMS, NX_MAX_FILE_SYSTEMS)
        self.fs_oids = [o for o in struct.unpack_from(f"<{n}Q", blk, _NX_FS_OID) if o]
        self.flags = _U64.unpack_from(blk, _NX_FLAGS)[0]
        self.keylocker = _PRANGE.unpack_from(blk, _NX_KEYLOCKER)


def _valid_block_size(bs: int) -> bool:
    return 4096 <= bs <= 65536 and bs & (bs - 1) == 0


class Container:
    """An opened APFS container (read-only)."""

    def __init__(self, ra: RandomAccess, ctx: Context) -> None:
        self.ra = ra
        self.ctx = ctx
        self.token = ctx.cache.token()
        head = ra.read_at(0, 4096)
        if len(head) < 4096 or head[32:36] != NX_MAGIC:
            raise CorruptDataError("apfs: no container superblock")
        bs = struct.unpack_from("<I", head, 36)[0]
        if not _valid_block_size(bs):
            raise CorruptDataError(f"apfs: invalid block size {bs}")
        self.block_size = bs
        blk0 = ra.read_at(0, bs)
        if len(blk0) < bs:
            raise CorruptDataError("apfs: truncated container superblock")
        sb0 = Superblock(blk0)
        self.nblocks = sb0.block_count
        sb0_ok = checksum_ok(blk0)
        best = self._latest_checkpoint(sb0)
        if best is None:
            if not sb0_ok:
                raise CorruptDataError("apfs: checksum mismatch in container superblock")
            best = sb0
        self.sb = best
        self.xid = best.xid
        self.omap = OMap(best.omap_oid, self.read_block, self.load_node, "container object map")
        self._vsb: dict[int, bytes] = {}
        self._keybag: Any = None

    # ----------------------------------------------------------------- blocks

    def read_blocks(self, paddr: int, count: int = 1) -> bytes:
        if paddr < 0 or count <= 0 or paddr + count > self.nblocks:
            raise CorruptDataError(f"apfs: invalid block address {paddr} (+{count})")
        return self.ra.read_exact(paddr * self.block_size, count * self.block_size)

    def read_block(self, paddr: int) -> bytes:
        return self.read_blocks(paddr, 1)

    def load_node(self, paddr: int, keyfn: Callable[[memoryview], Any], fixed: tuple[int, int] | None, what: str,
                  decrypt: Callable[[bytes, int], bytes] | None = None, size: int = 0, oid: int = 0) -> BNode:
        """Read, decrypt, verify and parse a B-tree node at ``paddr`` (cached)."""
        key = ("apfs-node", self.token, paddr)
        node = self.ctx.cache.get(key)
        if node is not None:
            return node  # type: ignore[return-value]
        n = max(1, size // self.block_size) if size else 1
        data = self.read_blocks(paddr, n)
        if decrypt is not None:
            data = decrypt(data, paddr)
        check_object(data, what)
        node = BNode(data, keyfn, fixed, what, oid or paddr)
        self.ctx.cache.put(key, node)
        return node

    def _latest_checkpoint(self, sb0: Superblock) -> Superblock | None:
        nblk = sb0.xp_desc_blocks
        if nblk & 0x80000000 or not nblk or nblk > 65536:
            return None   # non-contiguous (B-tree) descriptor area: use block 0
        base = sb0.xp_desc_base
        bs = self.block_size
        if base <= 0 or (base + nblk) * bs > self.ra.size:
            return None
        data = self.ra.read_at(base * bs, nblk * bs)
        best: Superblock | None = None
        mv = memoryview(data)
        for i in range(len(data) // bs):
            blk = mv[i * bs:(i + 1) * bs]
            if blk[32:36] != NX_MAGIC:
                continue
            otype = OBJ.unpack_from(blk, 0)[3] & OBJECT_TYPE_MASK
            if otype != OBJECT_TYPE_NX_SUPERBLOCK or not checksum_ok(blk):
                continue
            try:
                sb = Superblock(bytes(blk))
            except CorruptDataError:
                continue
            if sb.block_size != bs:
                continue
            if best is None or sb.xid > best.xid:
                best = sb
        return best

    # ---------------------------------------------------------------- volumes

    def volume_superblock(self, oid: int) -> bytes:
        blk = self._vsb.get(oid)
        if blk is None:
            m = self.omap.resolve(oid, self.xid, "volume superblock")
            blk = self.read_block(m.paddr)
            check_object(blk, "volume superblock")
            if blk[32:36] != APFS_MAGIC:
                raise CorruptDataError("apfs: bad volume superblock magic")
            self._vsb[oid] = blk
        return blk

    def keybag(self) -> Any:
        from .keybag import ContainerKeybag

        if self._keybag is None:
            self._keybag = ContainerKeybag.load(self)
        return self._keybag


class VolumeFacts:
    """Cheap facts from a volume superblock."""

    def __init__(self, blk: bytes) -> None:
        self.incompat = _U64.unpack_from(blk, _APSB_INCOMPAT)[0]
        self.fs_flags = _U64.unpack_from(blk, _APSB_FS_FLAGS)[0]
        self.uuid = bytes(blk[_APSB_UUID:_APSB_UUID + 16])
        self.name = blk[_APSB_VOLNAME:_APSB_VOLNAME + 256].split(b"\0", 1)[0].decode("utf-8", "replace")
        self.role_code = struct.unpack_from("<H", blk, _APSB_ROLE)[0]
        self.omap_oid, self.root_tree_oid = struct.unpack_from("<QQ", blk, _APSB_OMAP)
        self.alloc_blocks = _U64.unpack_from(blk, _APSB_ALLOC_COUNT)[0]

    @property
    def encrypted(self) -> bool:
        return not self.fs_flags & APFS_FS_UNENCRYPTED

    @property
    def onekey(self) -> bool:
        return bool(self.fs_flags & APFS_FS_ONEKEY)

    @property
    def case_insensitive(self) -> bool:
        return bool(self.incompat & APFS_INCOMPAT_CASE_INSENSITIVE)

    @property
    def role(self) -> str | None:
        return _ROLES.get(self.role_code, f"0x{self.role_code:x}")

    def extra(self) -> dict[str, Any]:
        return {
            "uuid": str(_uuid.UUID(bytes=self.uuid)),
            "role": self.role,
            "encrypted": self.encrypted,
            "case_sensitive": not self.case_insensitive,
        }


class APFSContainerSet(VolumeSet):
    format = "apfs"

    def __init__(self, c: Container) -> None:
        self.c = c
        n = len(c.sb.fs_oids)
        self.description = f"APFS container ({n} volume{'s' if n != 1 else ''}, {c.block_size}-byte blocks)"

    def volumes(self) -> Iterator[VolumeInfo]:
        c = self.c
        for i, oid in enumerate(c.sb.fs_oids):
            name = f"v{i + 1}"
            try:
                facts = VolumeFacts(c.volume_superblock(oid))
            except FsExplorerError as e:
                yield VolumeInfo(name, error=str(e), error_code=e.code)
                continue
            err = None
            if facts.encrypted and not facts.onekey:
                err = "encrypted with per-file (hardware-bound) keys"

            def opener(oid: int = oid) -> Any:
                return self.open_volume(oid)

            def label_loader(f: VolumeFacts = facts) -> str | None:
                return f.name or None

            yield VolumeInfo(
                name,
                opener=opener,
                size=facts.alloc_blocks * c.block_size or None,
                extra=facts.extra(),
                error=err,
                error_code="unsupported_format" if err else None,
                label_loader=label_loader,
            )

    def open_volume(self, oid: int) -> Any:
        from .fs import APFSVolume

        blk = self.c.volume_superblock(oid)
        facts = VolumeFacts(blk)
        if facts.encrypted and not facts.onekey:
            raise UnsupportedFormatError("apfs", f'volume "{facts.name}": per-file (hardware-bound) keys')
        return APFSVolume(self.c, blk)


class APFSDriver(Driver):
    name = "apfs"
    layer = Layer.FILESYSTEM
    extensions = (".apfs",)

    @classmethod
    def probe(cls, hint: ProbeHint) -> int:
        if hint.at(32, 4) != NX_MAGIC:
            return 0
        bs = struct.unpack("<I", hint.at(36, 4))[0]
        if not _valid_block_size(bs):
            return 30
        blk = hint.at(0, bs)
        if len(blk) == bs and checksum_ok(blk):
            return 95
        return 70

    @classmethod
    def open(cls, ra: RandomAccess, ctx: Context, hint: ProbeHint) -> APFSContainerSet:
        return APFSContainerSet(Container(ra, ctx))
