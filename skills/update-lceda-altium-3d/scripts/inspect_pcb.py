"""Inventory PCB or ZIP/epro2 without modifying/extracting the input."""
import argparse
import collections
import json
import zipfile
from pathlib import Path
from pcb_data import read_pcb, sha256


def inspect(path):
    path = Path(path)
    if zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            entries = [{'name': i.filename, 'bytes': i.file_size} for i in archive.infolist()]
        return {'format': 'ZIP container', 'sha256': sha256(path), 'entries': entries,
                'note': 'Inspect project2.json/epru and select a matching Altium PCB export; this is not a conversion.'}
    report = read_pcb(path)
    report.pop('records')
    report['footprint_counts'] = dict(collections.Counter(p['PATTERN'] for p in report['components']))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    text = json.dumps(inspect(args.input), ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(text, encoding='utf8')
    else:
        print(text)
