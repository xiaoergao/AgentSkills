"""Read LCEDA Altium exports; scope: ASCII records and PCB6 OLE component blocks."""
import hashlib
import re
import struct
from pathlib import Path


def sha256(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def blocks(data):
    position = 0
    result = []
    while position < len(data):
        if position + 4 > len(data):
            raise ValueError('Truncated parameter block length')
        length = struct.unpack_from('<I', data, position)[0]
        end = position + 4 + length
        if end > len(data):
            raise ValueError('Truncated parameter block')
        result.append(data[position + 4:end])
        position = end
    return result


def parameters(data):
    if isinstance(data, bytes):
        data = data.rstrip(b'\0').decode('latin1')
    return dict(field.split('=', 1) for field in data.strip('|\r\n').split('|') if '=' in field)


def millimetres(value):
    match = re.fullmatch(r'\s*([+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?)\s*(mil|mm)\s*', value, re.I)
    if not match:
        raise ValueError('Expected explicit mil/mm units: ' + value)
    return float(match[1]) * (0.0254 if match[2].lower() == 'mil' else 1)


def read_pcb(path):
    path = Path(path)
    with path.open('rb') as f:
        binary = f.read(8) == bytes.fromhex('d0cf11e0a1b11ae1')
    if binary:
        import olefile
        with olefile.OleFileIO(str(path)) as ole:
            parts = [parameters(row) for row in blocks(ole.openstream('Components6/Data').read())]
            counts = {}
            for item in ('Components6', 'ComponentBodies6', 'Models', 'Pads6', 'Vias6', 'Nets6', 'Tracks6', 'Arcs6', 'Polygons6'):
                if ole.exists(item + '/Header'):
                    counts[item] = struct.unpack('<I', ole.openstream(item + '/Header').read())[0]
        records = []
    else:
        records = [parameters(line) for line in path.read_text(encoding='latin1').splitlines() if line.startswith('|RECORD=')]
        parts = [row for row in records if row.get('RECORD') == 'Component']
        counts = {kind: sum(row.get('RECORD') == kind for row in records)
                  for kind in ('Component', 'ComponentBody', 'Pad', 'Via', 'Net', 'Track', 'Arc', 'Polygon')}
    if not parts:
        raise ValueError('No supported PCB components found')
    refs = [p['SOURCEDESIGNATOR'] for p in parts]
    if len(set(refs)) != len(refs):
        raise ValueError('Duplicate component designators')
    for p in parts:
        millimetres(p['X'])
        millimetres(p['Y'])
        if p['LAYER'] not in ('TOP', 'BOTTOM'):
            raise ValueError('Unsupported component layer: ' + p['LAYER'])
    return {'format': 'OLE PCB6' if binary else 'Altium ASCII', 'components': parts,
            'counts': counts, 'records': records, 'sha256': sha256(path)}
