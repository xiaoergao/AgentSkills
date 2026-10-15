"""Compact AD PCB6 embedded STEP geometry on Windows; never overwrite the input.

Same model names must have byte-identical payloads. Every body's position,
rotation and height stay local. All unrelated object streams are copied intact.
"""
import argparse
import ctypes as C
import json
import os
from pathlib import Path
import re
import struct
import uuid
import olefile
from pcb_data import blocks, sha256

U32, POINTER, WIDE, HRESULT = C.c_uint32, C.c_void_p, C.c_wchar_p, C.c_long
GUID = rb'\{[0-9A-Fa-f-]{36}\}'


def method(obj, index, result, arguments):
    return C.WINFUNCTYPE(result, POINTER, *arguments)(C.cast(obj, C.POINTER(C.POINTER(POINTER))).contents[index])


def checked(hr):
    if hr < 0:
        raise OSError('Structured-storage HRESULT ' + hex(hr & 0xffffffff))


def release(obj):
    method(obj, 2, U32, [])(obj)


def create_storage(parent, name):
    obj = POINTER()
    checked(method(parent, 5, HRESULT, [WIDE, U32, U32, U32, C.POINTER(POINTER)])(parent, name, 0x12, 0, 0, C.byref(obj)))
    return obj


def write_stream(parent, name, data):
    obj = POINTER()
    checked(method(parent, 3, HRESULT, [WIDE, U32, U32, U32, C.POINTER(POINTER)])(parent, name, 0x12, 0, 0, C.byref(obj)))
    try:
        written, buffer = U32(), C.create_string_buffer(data)
        checked(method(obj, 4, HRESULT, [POINTER, U32, C.POINTER(U32)])(obj, buffer, len(data), C.byref(written)))
        if written.value != len(data):
            raise OSError('Incomplete structured-storage write')
    finally:
        release(obj)


def write_ole(path, streams, clsids=None, storages=()):
    if os.name != 'nt':
        raise RuntimeError('Windows ole32 is required for compound-storage writing')
    ole32 = C.OleDLL('ole32')
    initialized = ole32.CoInitializeEx(None, 2)
    if initialized < 0 and initialized != -2147417850:  # RPC_E_CHANGED_MODE: COM already initialized.
        checked(initialized)
    ole32.StgCreateDocfile.argtypes = [WIDE, U32, U32, C.POINTER(POINTER)]
    ole32.StgCreateDocfile.restype = HRESULT
    root = POINTER()
    objects = {}
    try:
        checked(ole32.StgCreateDocfile(str(path), 0x1012, 0, C.byref(root)))
        objects[()] = root
        all_storages = set(storages)
        for key in streams:
            for length in range(1, len(key)):
                all_storages.add(key[:length])
        for key in sorted(all_storages, key=lambda k: (len(k), k)):
            objects[key] = create_storage(objects[key[:-1]], key[-1])
        for key, obj in objects.items():
            if clsids and clsids.get(key):
                raw = C.create_string_buffer(uuid.UUID(clsids[key]).bytes_le)
                checked(method(obj, 15, HRESULT, [POINTER])(obj, raw))
        for key, data in streams.items():
            write_stream(objects[key[:-1]], key[-1], data)
        checked(method(root, 9, HRESULT, [U32])(root, 0))
    finally:
        for obj in reversed(list(objects.values())):
            release(obj)
        if initialized >= 0:
            ole32.CoUninitialize()


def packblocks(items):
    return b''.join(struct.pack('<I', len(item)) + item for item in items)


def compact(source, target):
    source, target = Path(source).resolve(), Path(target).absolute()
    if source == target.resolve() or target.exists():
        raise ValueError('Output must be a new file, distinct from input')
    source_hash = sha256(source)
    with olefile.OleFileIO(str(source)) as ole:
        original = {tuple(p): ole.openstream(p).read() for p in ole.listdir()}
        clsids = {tuple(ole.getpath(i)) if i else (): entry.clsid for i, entry in enumerate(ole.direntries)
                  if entry and entry.entry_type in (1, 5) and entry.clsid}
        storages = [tuple(p) for p in ole.listdir(streams=False, storages=True)]
    streams = original.copy()
    rows = blocks(streams[('Models', 'Data')])
    if len(rows) != struct.unpack('<I', streams[('Models', 'Header')])[0]:
        raise ValueError('Model count/header mismatch')
    groups, identity_map, identity_geometry, retained = {}, {}, {}, []
    for index, row in enumerate(rows):
        fields = dict(t.split(b'=', 1) for t in row.rstrip(b'\0').split(b'|') if b'=' in t)
        name, identity = fields[b'NAME'], fields[b'ID']
        if fields.get(b'EMBED') != b'TRUE' or not re.fullmatch(GUID, identity):
            raise ValueError('Only embedded STEP records with GUID identities are supported')
        payload = streams[('Models', str(index))]
        if identity in identity_geometry and identity_geometry[identity] != payload:
            raise ValueError('Conflicting geometry under one model identity')
        identity_geometry[identity] = payload
        if name not in groups:
            groups[name] = (identity, payload)
            retained.append((row, payload))
        elif payload != groups[name][1]:
            raise ValueError('Same model name has different geometry: ' + repr(name))
        identity_map[identity] = groups[name][0]
    before_bodies = streams[('ComponentBodies6', 'Data')]
    referenced = set(re.findall(rb'MODELID=(' + GUID + rb')', before_bodies))
    if referenced - set(identity_map):
        raise ValueError('Body references an undefined model')
    bodies = re.sub(rb'MODELID=(' + GUID + rb')', lambda match: b'MODELID=' + identity_map[match[1]], before_bodies)
    if len(bodies) != len(before_bodies):
        raise ValueError('Body record lengths changed')
    streams[('ComponentBodies6', 'Data')] = bodies
    streams = {k: v for k, v in streams.items() if not (len(k) == 2 and k[0] == 'Models' and k[1].isdigit())}
    streams[('Models', 'Data')] = packblocks([row for row, payload in retained])
    streams[('Models', 'Header')] = struct.pack('<I', len(retained))
    for index, (row, payload) in enumerate(retained):
        streams[('Models', str(index))] = payload
    temporary = target.with_name(target.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        write_ole(temporary, streams, clsids, storages)
        with olefile.OleFileIO(str(temporary)) as ole:
            if set(tuple(p) for p in ole.listdir()) != set(streams):
                raise RuntimeError('Written stream inventory mismatch')
            for key, value in streams.items():
                if ole.openstream(key).read() != value:
                    raise RuntimeError('Written stream mismatch: ' + repr(key))
        if sha256(source) != source_hash:
            raise RuntimeError('Input changed during compaction')
        temporary.rename(target)
    finally:
        if temporary.exists():
            temporary.unlink()  # Only the exact new temporary file, never an input or directory.
    report = {'source_bytes': source.stat().st_size, 'compacted_bytes': target.stat().st_size,
              'body_count': struct.unpack('<I', streams[('ComponentBodies6', 'Header')])[0],
              'unique_embedded_models': len(retained), 'referenced_models': len(set(identity_map[g] for g in referenced)),
              'unmodified_object_streams': sum(k[0] != 'Models' and k != ('ComponentBodies6', 'Data') for k in original),
              'source_sha256': source_hash, 'output_sha256': sha256(target)}
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    report = compact(args.input, args.output)
    args.output.with_suffix('.dedup.json').write_text(json.dumps(report, indent=2), encoding='utf8')
