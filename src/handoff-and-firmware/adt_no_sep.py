# SPDX-License-Identifier: GPL-2.0-or-later
"""Bounded Apple Device Tree edit for an emulated platform without a SEP.

Wire-format and guest-contract reference: qemu-reims-vgpu e1c37ea4d4a74f.
This module does not change a kernel, firmware file, or physical device.
"""
import struct


class TreeError(ValueError):
    pass


def _node(data, offset, limit, depth=0):
    if depth > 64 or offset + 8 > limit:
        raise TreeError('Invalid node bounds or nesting')
    count, children = struct.unpack_from('<II', data, offset)
    cursor = offset + 8
    properties = {}
    for _ in range(count):
        if cursor + 36 > limit:
            raise TreeError('Truncated property header')
        field = data[cursor:cursor + 32]
        if b'\0' not in field:
            raise TreeError('Unterminated property name')
        try:
            name = field.split(b'\0', 1)[0].decode('ascii')
        except UnicodeDecodeError as error:
            raise TreeError('Non-ASCII property name') from error
        if not name or name in properties:
            raise TreeError('Empty or duplicate property name')
        size = struct.unpack_from('<I', data, cursor + 32)[0] & 0x7fffffff
        end = cursor + 36 + ((size + 3) & ~3)
        if end > limit:
            raise TreeError('Property extends outside declared tree')
        properties[name] = bytes(data[cursor + 36:cursor + 36 + size])
        cursor = end
    nodes = []
    for _ in range(children):
        node, cursor = _node(data, cursor, limit, depth + 1)
        nodes.append(node)
    return {'properties': properties, 'children': nodes}, cursor


def _property(name, value):
    encoded = name.encode('ascii')
    if not encoded or len(encoded) >= 32:
        raise TreeError('Invalid output property name')
    return encoded.ljust(32, b'\0') + struct.pack('<I', len(value)) + value.ljust((len(value) + 3) & ~3, b'\0')


def add_no_sep(reserved, declared_length):
    """Return (reserved bytes, new declared length, changed), failing before mutation.

    `reserved` must describe only the tree's existing reserved guest-memory
    region. The caller establishes that region's physical RAM bounds.
    """
    if declared_length < 8 or declared_length > len(reserved) or len(reserved) > 4 * 1024**2:
        raise TreeError('Invalid tree reservation')
    root, end = _node(reserved, 0, declared_length)
    matches = [node for node in root['children'] if node['properties'].get('name') == b'filesystems\0']
    if len(matches) > 1:
        raise TreeError('Duplicate filesystems nodes')
    if matches:
        if matches[0]['properties'].get('DoNotUseSEP') != struct.pack('<I', 1):
            raise TreeError('Existing filesystems contract requires inspection')
        return bytes(reserved), declared_length, False
    node = struct.pack('<II', 2, 0) + _property('name', b'filesystems\0') + _property('DoNotUseSEP', struct.pack('<I', 1))
    if end + len(node) > len(reserved):
        raise TreeError('No reserved room for filesystems node')
    if any(reserved[end:max(declared_length, end + len(node))]):
        raise TreeError('Tree padding contains data')
    child_count = struct.unpack_from('<I', reserved, 4)[0]
    if child_count == 0xffffffff:
        raise TreeError('Child count overflows')
    result = bytearray(reserved)
    result[end:end + len(node)] = node
    struct.pack_into('<I', result, 4, child_count + 1)
    new_length = max(declared_length, end + len(node))
    parsed, consumed = _node(result, 0, new_length)
    if consumed > new_length or not parsed['children']:
        raise TreeError('Output tree validation failed')
    return bytes(result), new_length, True
