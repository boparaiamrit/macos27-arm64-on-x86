# SPDX-License-Identifier: GPL-2.0-or-later
import struct
import unittest

from adt_no_sep import TreeError, add_no_sep


def prop(name, value):
    return name.encode().ljust(32, b'\0') + struct.pack('<I', len(value)) + value + b'\0' * (-len(value) % 4)


def node(name, children=(), extra=()):
    properties = [prop('name', name.encode() + b'\0'), *extra]
    return struct.pack('<II', len(properties), len(children)) + b''.join(properties) + b''.join(children)


class NoSepTests(unittest.TestCase):
    def test_append_keeps_existing_nodes_and_is_idempotent(self):
        original = node('root', [node('chosen', extra=[prop('marker', b'KEEP')])])
        reserved = original.ljust(512, b'\0')
        edited, length, changed = add_no_sep(reserved, len(original))
        self.assertTrue(changed)
        self.assertEqual(edited[8:len(original)], original[8:])
        self.assertEqual(struct.unpack_from('<I', edited, 4)[0], 2)
        self.assertIn(b'DoNotUseSEP', edited[len(original):length])
        self.assertEqual(add_no_sep(edited, length), (edited, length, False))

    def test_existing_valid_contract_is_untouched(self):
        original = node('root', [node('filesystems', extra=[prop('DoNotUseSEP', b'\x01\0\0\0')])])
        self.assertEqual(add_no_sep(original, len(original)), (original, len(original), False))

    def test_existing_different_contract_is_rejected(self):
        original = node('root', [node('filesystems')])
        with self.assertRaises(TreeError):
            add_no_sep(original.ljust(512, b'\0'), len(original))

    def test_duplicate_contract_nodes_are_rejected(self):
        original = node('root', [node('filesystems'), node('filesystems')])
        with self.assertRaises(TreeError):
            add_no_sep(original.ljust(512, b'\0'), len(original))

    def test_no_room_is_rejected_without_mutating_input(self):
        original = bytearray(node('root'))
        copy = bytes(original)
        with self.assertRaises(TreeError):
            add_no_sep(original, len(original))
        self.assertEqual(bytes(original), copy)

    def test_nonzero_padding_is_rejected(self):
        original = node('root')
        reserved = original + b'\xff' + bytes(512)
        with self.assertRaises(TreeError):
            add_no_sep(reserved, len(original))

    def test_truncated_or_oversized_property_is_rejected(self):
        malformed = struct.pack('<II', 1, 0) + b'name'.ljust(32, b'\0') + struct.pack('<I', 0x7fffffff)
        with self.assertRaises(TreeError):
            add_no_sep(malformed.ljust(512, b'\0'), len(malformed))

    def test_declared_padding_is_reused_without_shrinking(self):
        original = node('root')
        edited, length, changed = add_no_sep(original.ljust(512, b'\0'), 256)
        self.assertTrue(changed)
        self.assertEqual(length, 256)
        self.assertEqual(len(edited), 512)


if __name__ == '__main__':
    unittest.main()
