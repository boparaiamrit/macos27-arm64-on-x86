# ASIF binary specification

With macOS 26, Apple introduced the Apple Sparse Image Format (ASIF) for virtual disks.

As usual, there are no technical details provided about the layout of the ASIF file.

This repository collects reverse-engineered technical details and community-contributed findings about the Apple Sparse Image Format ASIF, for the benefit of forensics engineers, virtualization tool authors, archivists, and researchers.

ASIF is a two‑level indirect block scheme.

This file documents ASIF with header version 1.

## Header

Integers are stored in big‑endian order.

| Offset (hex) | Length (bytes) | Description                         |
|--------------|----------------|-------------------------------------|
| 0x00         | 4              | Magic 'shdw' (73 68 64 77)          |
| 0x04         | 4              | Version (ex.: 00 00 00 01)          |
| 0x08         | 4              | Header size (ex.: 00 00 02 00)      |
| 0x0C         | 4              | Flags                               |
| 0x10         | 8              | Offset to Directory (bytes)         |
| 0x18         | 8              | Offset to Directory (bytes)         |
| 0x20         | 16             | UUID                                |
| 0x30         | 8              | Sector count                        |
| 0x38         | 8              | Maximum sector count                |
| 0x40         | 4              | Chunk size (bytes); must be a non-zero multiple of block size                  |
| 0x44         | 2              | Block size (bytes); must be a non-zero multiple of 512           |
| 0x46         | 2              | `00 00`; Apple’s ASIF parser labels this field `total_segments_t` and rejects non-zero values                                 |
| 0x48         | 8              | Metadata offset (unit: chunk size)  |

### Definitions

Let N be the number of data chunks per chunk‑group.  
Let S be the size of a chunk‑group in bytes.  
Let C be the number of chunk‑groups that fit into a single table.  
Let D be the total amount of data addressed by one table.  
Let T be the maximum number of tables required for the image.

```
N = 4 * block size
S = 8 * (N + 1)  
C = floor(chunk size / S)  
D = C * N * chunk size  
T = ceil(max sector count * block size / D)
```

## Directory

The header references two directories. The directory with the highest sequence number is considered the active one.

To locate a table for a given logical offset, divide the offset by D (the data range covered by a single table). The integer quotient yields the index into the directory; the corresponding entry provides the chunk number that holds the desired table.

A directory entry value of `0` indicates that no table is present; readers should treat the entire data range covered by the table as sparse zeroes. Do not interpret directory entry `0` as a chunk number (chunk `0` contains the header and directories).

| Offset (hex) | Length (bytes) | Description                          |
|--------------|----------------|--------------------------------------|
| 0x00         | 8              | Sequence number                      |
| 0x08         | 8              | Chunk number that contains Table 0   |
| 0x10         | 8              | Chunk number that contains Table 1   |
...
| 8 * T        | 8              | Chunk number that contains Table T-1 |

## Table

Each table is composed of C chunk‑groups placed sequentially. To determine the chunk-group, divide the relative offset by N * chunk size (the data range covered by a single chunk-group).

| Offset (hex)   | Length (bytes) | Description                         |
|----------------|----------------|-------------------------------------|
| 0x00           | S              | Chunk group 0                       |
| S              | S              | Chunk group 1                       |
...
| S * (C - 1)    | S              | Chunk group C-1                     |

## Chunk Group

A chunk-group stores N data-chunk references followed by a single bitmap-chunk reference. The most-significant nine bits of each chunk number are reserved for flag bits. The remaining 55 bits represent the physical chunk index.

To determine the data chunk number, divide the relative offset by chunk size.

| Offset (hex) | Length (bytes) | Description                         |
|--------------|----------------|-------------------------------------|
| 0x00         | 8              | Data chunk 0                        |
| 0x08         | 8              | Data chunk 1                        |
...
| 8 * (N - 1)  | 8              | Data chunk N-1                      |
| 8 * N        | 8              | Bitmap chunk                        |

### Chunk Entry Flags

The high 9 bits of each 64-bit chunk entry are flags; the low 55 bits are the physical chunk index. The value of bits 63-62 has observed meaning for data chunks.

| Bit(s) | Mask                 | Label             |
|--------|----------------------|-------------------|
| 63-62  | 0xC000000000000000   | Data chunk status |
| 61-55  | 0x3F80000000000000   | Reserved          |

```
Data chunk status = entry >> 62
Physical chunk index = entry & 0x007FFFFFFFFFFFFF
```

### Observed behavior

- Completely uninitialized data chunks have `Data chunk status` = `00` and physical chunk index = `0`.
- Partially initialized data chunks have `Data chunk status` = `11`; the corresponding sector states are stored in the bitmap chunk.
- Completely initialized data chunks have `Data chunk status` = `01`; the corresponding bitmap range is not used for sector validity.
- Unmapped data chunks have `Data chunk status` = `10` and physical chunk index = `0`; this was observed after `DKIOCUNMAP` and reads as sparse zeroes.
- Bitmap chunk entries are not data chunk entries; they have been observed with high bits clear while still pointing to an allocated bitmap chunk.
- A chunk-group containing no partially initialized (`Data chunk status` = `11`) data chunks does not need an allocated bitmap chunk; after writing one complete data chunk to an otherwise empty image, the bitmap chunk entry remained `0`.
- Images created from a folder by `diskutil image create ... from --format ASIF` have been observed with a payload size that is not a multiple of the chunk size. In one image with 1 MiB chunks and 512-byte sectors, the header `sector count` was `8268` sectors (`4 * 2048 + 76`), so the logical disk ended 76 sectors into a data chunk rather than being rounded up to the next chunk boundary. The backing payload also ended 76 sectors into its final physical chunk. The final logical data chunk referenced this truncated physical chunk with a partial data-chunk entry. Within the 76 logical sectors in that chunk, observed bitmap states were initialized (`01`) for sectors 0-33 and 40-75, and sparse (`00`) for sectors 34-39. Bitmap states beyond the header `sector count` should not be used to extend the logical disk; they are outside the image's logical size.

## Bitmap Chunk

The bitmap chunk is likely a 2-bits-per-sector map for the entire chunk-group.

From the definitions above:

- Chunk-group data size = `N * chunk size`
- Sectors per chunk-group = `(N * chunk size) / block size` = `4 * chunk size`
- At 2 bits per sector, bitmap size = `(4 * chunk size * 2) / 8` = `chunk size`

This matches the bitmap chunk size exactly.

Observed behavior in sample images:

- Writes to bitmap-backed chunks set the corresponding 2-bit sector state to `01`; a bitmap byte becomes `0x55` when all four packed sector states are `01`.
- Partial `DKIOCUNMAP` of a previously initialized data chunk sets the corresponding 2-bit sector state to `10`; a bitmap byte becomes `0xAA` when all four packed sector states are `10`.
- A write at sector 2048 changed the bitmap byte at offset `0x200` (since `2048 / 4 = 0x200`). Sector 2047 mapped to `0x1ff`.
- In a test image with 1 MiB chunks and 512-byte sectors, writing one full data chunk and then issuing `DKIOCUNMAP` for bytes `262144..<524288` converted the data chunk entry from initialized (`01`) to partial (`11`). The referenced bitmap chunk contained runs of 512 sectors `01`, 512 sectors `10`, and 1024 sectors `01`.
- Reads through Apple's disk image stack returned zeroes for the bitmap sectors marked `10`, even though the referenced physical data chunk still contained the old written bytes. This indicates that bitmap state `10` is metadata-level unmapped/sparse state, not an instruction to read backing data.

Byte layout (one byte = 4 sectors):

```
bit:  7 6  5 4  3 2  1 0
      [s3] [s2] [s1] [s0]
```

Each byte packs four 2-bit tuples for four consecutive sectors. The ordering is LSB-first: sector 0 uses bits 1:0, sector 1 uses bits 3:2, sector 2 uses bits 5:4, and sector 3 uses bits 7:6. The metadata bitmap byte `0x05` at offset `0xFFE00` implies the first two sectors in that 4-sector group are set, which matches the 0x200-byte metadata header plus plist data.

Addressing formula:

```
byte offset = floor(sector index / 4)
bit pair = (sector index % 4) * 2
state = (bitmap byte >> bit pair) & 0x3
```

| Bits | Label   | Notes                                             |
|------|---------|---------------------------------------------------|
| 00   | State 0 | Observed in untouched sectors.                    |
| 01   | State 1 | Observed where sectors have data written.         |
| 10   | State 2 | Observed after partial `DKIOCUNMAP`; sectors read as sparse zeroes. |
| 11   | State 3 | Not observed as a valid sector state; Apple's parser reports "bitmap flag value invalid". |

Sectors marked `00` or `10` should be treated as sparse (returning all zeros on read). Sectors marked `01` should be read from the referenced physical data chunk. State `11` should be treated as invalid/unsupported in a bitmap; Apple's parser reports "bitmap flag value invalid" for this state.

## Implementation notes

Some states are unknown / not yet observed:

- `Data chunk status` = `00` with physical chunk index > `0`
- `Data chunk status` = `10` with physical chunk index > `0`
- `Data chunk status` = `11` with bitmap sector state `11`

Until these states have been characterized, readers should treat them as unsupported rather than returning guessed data.

### Readers

Suggested read behavior for known states:

- `Data chunk status` = `00` and physical chunk index = `0`: return all zeros for sectors in the data chunk
- `Data chunk status` = `10` and physical chunk index = `0`: return all zeros for sectors in the data chunk
- `Data chunk status` = `11`: consult the corresponding sector status in the bitmap chunk; return all zeros for uninitialized sectors (`00`) and unmapped sectors (`10`), read physical chunk for initialized sectors (`01`), and reject bitmap state `11`.
- `Data chunk status` = `01`: read physical chunk

Readers should use the header `sector count` as the exact logical disk size. Observed images may end partway through a data chunk; readers should not round the logical size up to the next chunk boundary.

Readers should not reject an image solely because the backing ASIF payload size is not a multiple of the chunk size. Bound guest-visible disk data requests by the header `sector count` first, then consult the bitmap for sectors in partial data chunks that are still within that logical range. Sectors marked sparse (`00` or `10`) should read as zeroes. Sectors marked initialized (`01`) must be readable from the referenced physical chunk; if the physical byte range is beyond the backing payload, treat the image as invalid or unsupported.

### Writers

Suggested data chunk state after completing a write operation:

- If some, but not all, sectors in the data chunk are initialized: set `Data chunk status` = `11`, set the physical chunk index to the data chunk, and update the corresponding sector status in the bitmap chunk.
- If all sectors in the data chunk are initialized: set `Data chunk status` = `01` and set the physical chunk index to the data chunk. The corresponding bitmap range does not need to be updated for sector validity.
- If the data chunk is unmapped/discarded: set `Data chunk status` = `10` and physical chunk index = `0`. Previously referenced physical data may remain present in the file but unreferenced.
- If only part of a data chunk is unmapped/discarded: set `Data chunk status` = `11`, keep or allocate a physical data chunk and bitmap chunk as needed, and mark the discarded sectors in the bitmap as `10`.
- Writes to sectors in a partial data chunk should mark the written sectors as `01`. Existing `10` sectors outside the written range should remain `10`. If a later write initializes every sector and changes the data chunk status to `01`, the bitmap range is no longer used for that data chunk.

Writers should preserve bits 61-55 (Reserved) when updating existing entries and set them to zero when creating new entries.

Logical growth is sector-based, not chunk-based. Writers may increase the header `sector count` to a value that ends partway through a data chunk, and may append only a partial physical chunk when doing so. A writer may choose to grow in full chunks for implementation convenience. If the backing payload already ends with a partial physical chunk referenced by a logical data chunk, that physical chunk index must not be reused for a different logical chunk. A writer may continue writing the same logical chunk into that physical chunk, or it may leave sectors sparse/uninitialized through bitmap states `00` or `10` and start an unrelated physical chunk at the next chunk boundary.

When a writer does need to append a new physical chunk that is not a continuation of the truncated trailing physical chunk's logical data chunk, it should choose the next physical chunk index as `ceil(payload size / chunk size)`, not `floor(payload size / chunk size)`. This avoids reusing a truncated final physical chunk as if it were free space for an unrelated logical chunk.

## Metadata

An ASIF image contains metadata consisting of a header and property list (XML). To read the metadata, use offset

> metadata offset * chunk size

This offset is a logical address and must be resolved through the directory/table mapping. In observed images, the metadata offset points into the last directory entry (T-1), which references a small table in chunk 1. That table entry then points to the metadata chunk (for example, chunk 2 at byte offset `0x00200000`). Note that this logical address can be past the current sector count, but still within the maximum sector count (typically the theoretically last chunk of the image).

### Metadata header

| Offset (hex) | Length (bytes) | Description                         |
|--------------|----------------|-------------------------------------|
| 0x00         | 4              | Magic 'meta' (6d 65 74 61)          |
| 0x04         | 4              | Version (ex.: 00 00 00 01)          |
| 0x08         | 4              | Header size (ex.: 00 00 02 00)      |
| 0x0C         | 8              | Offset to metadata property list (bytes)    |

Note: The offset is [not 8-byte aligned](https://github.com/fox-it/dissect.hypervisor/issues/73).

### Metadata property list

The [property list](https://en.wikipedia.org/wiki/Property_list) is an XML dictionary. In observed images it contains:

| Key               | Type  | Notes                                              |
|-------------------|-------|----------------------------------------------------|
| internal metadata | dict  | Contains a `stable uuid` string.                   |
| user metadata     | dict  | Present but empty in observed images.              |

`stable uuid` is a UUID string (unique per image).

Example:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>internal metadata</key>
	<dict>
		<key>stable uuid</key>
		<string>dc5c7a3b-1915-43c2-944d-46c6c304b3b7</string>
	</dict>
	<key>user metadata</key>
	<dict/>
</dict>
</plist>
```

## Creating Test Images

```
$ diskutil image create blank --format ASIF --size 123g -fs None test.asif
$ diskutil image info test.asif 
```

## Testing Write

```
diskutil image attach --noMount  test.asif
echo -n 1 | dd of=/dev/disk27 bs=1 count=1
hdiutil eject /dev/disk27
```

## References

- Python implementation by Fox-IT:
    - [asif.py](https://github.com/fox-it/dissect.hypervisor/blob/main/dissect/hypervisor/disk/asif.py)
    - [c_asif.py](https://github.com/fox-it/dissect.hypervisor/blob/main/dissect/hypervisor/disk/c_asif.py)

## Contributing

If you spot omissions or errors, or have additional findings to share, please open an issue or submit a pull request.
