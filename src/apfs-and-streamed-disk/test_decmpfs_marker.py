"""Protocol fixtures for stored decmpfs types, independent of Apple file bytes."""
import struct
import unittest

from fs_explorer.filesystems.decmpfs import open_compressed
from fs_explorer.io.source import BytesRA
from fs_explorer.errors import CorruptDataError


class StoredDecmpfsTests(unittest.TestCase):
    def test_type9_inline_marker_is_not_file_data(self):
        body = b'<?xml version="1.0"?><plist></plist>\n'
        attribute = struct.pack('<4sIQ', b'fpmc', 9, len(body)) + b'\xcc' + body
        source = open_compressed(attribute, lambda: None, None)
        self.assertEqual(source.read_at(0, len(body)), body)

    def test_type10_resource_markers_are_not_file_data(self):
        first, second = b'A' * 65536, b'end'
        table = struct.pack('<III', 12, 12 + 1 + len(first), 12 + 2 + len(first) + len(second))
        resource = BytesRA(table + b'\xcc' + first + b'\xcc' + second)
        attribute = struct.pack('<4sIQ', b'fpmc', 10, len(first) + len(second))
        source = open_compressed(attribute, lambda: resource, None)
        self.assertEqual(source.read_at(65530, 9), b'A' * 6 + b'end')

    def test_type1_plain_data_retains_a_literal_cc(self):
        body = b'\xccliteral binary data'
        attribute = struct.pack('<4sIQ', b'fpmc', 1, len(body)) + body
        source = open_compressed(attribute, lambda: None, None)
        self.assertEqual(source.read_at(0, len(body)), body)

    def test_type9_missing_marker_or_wrong_length_is_rejected(self):
        for payload in (b'ABC', b'\xccAB', b'\xccABCD'):
            attribute = struct.pack('<4sIQ', b'fpmc', 9, 3) + payload
            with self.subTest(payload=payload), self.assertRaises(CorruptDataError):
                source = open_compressed(attribute, lambda: None, None)
                source.read_at(0, 3)


if __name__ == '__main__':
    unittest.main()
