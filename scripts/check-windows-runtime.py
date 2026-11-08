#!/usr/bin/env python3
"""Reject portable Windows executables that require an unbundled VC runtime."""
from pathlib import Path
import re
import struct
import sys


def imported_dlls(path):
    if not 0 < path.stat().st_size <= 512 * 1024 * 1024:
        raise ValueError('invalid executable size')
    data = path.read_bytes()

    def unpack(fmt, offset):
        if offset < 0 or offset + struct.calcsize(fmt) > len(data):
            raise ValueError('truncated PE header')
        return struct.unpack_from(fmt, data, offset)

    if data[:2] != b'MZ':
        raise ValueError('missing DOS header')
    pe, = unpack('<I', 0x3c)
    if data[pe:pe + 4] != b'PE\0\0':
        raise ValueError('missing PE signature')
    machine, sections = unpack('<HH', pe + 4)
    optional_size, = unpack('<H', pe + 20)
    optional = pe + 24
    magic, = unpack('<H', optional)
    if machine != 0x8664 or magic != 0x20b or optional_size < 128:
        raise ValueError('expected a Windows x64 PE32+ executable')
    directories, = unpack('<I', optional + 108)
    if directories < 2:
        raise ValueError('missing import directory')
    import_rva, import_size = unpack('<II', optional + 120)
    if not import_rva or import_size < 20:
        raise ValueError('missing import table')
    mappings = []
    for index in range(sections):
        section = optional + optional_size + index * 40
        virtual_size, address, raw_size, pointer = unpack('<IIII', section + 8)
        mappings.append((address, max(virtual_size, raw_size), pointer, raw_size))

    def file_offset(rva, size):
        for address, virtual_size, pointer, raw_size in mappings:
            relative = rva - address
            if 0 <= relative < virtual_size and relative + size <= raw_size:
                offset = pointer + relative
                if offset + size <= len(data):
                    return offset
        raise ValueError('import RVA is outside file-backed sections')

    dlls = []
    for index in range(min(import_size // 20, 1024)):
        descriptor = unpack('<IIIII', file_offset(import_rva + index * 20, 20))
        if not any(descriptor):
            return dlls
        offset = file_offset(descriptor[3], 1)
        end = data.find(b'\0', offset, min(offset + 260, len(data)))
        if end == -1:
            raise ValueError('unterminated DLL name')
        dlls.append(data[offset:end].decode('ascii'))
    raise ValueError('unterminated import table')


if __name__ == '__main__':
    try:
        names = imported_dlls(Path(sys.argv[1]))
        external = [name for name in names if re.match(r'^(vcruntime|msvcp|msvcr|concrt)\d', name, re.I)]
        if external:
            raise ValueError('portable executable requires external Visual C++ runtime: ' + ', '.join(external))
        print('Windows PE imports verified: no Visual C++ runtime DLL dependency')
    except (IndexError, OSError, ValueError, struct.error) as exc:
        raise SystemExit(str(exc)) from exc
