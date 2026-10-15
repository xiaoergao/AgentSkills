"""One action: snapshot a PcbDoc and run native KiCad import in a new directory."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def digest(path):
    with Path(path).open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def run(source, cli, out):
    source, cli, out = Path(source).resolve(), Path(cli).resolve(), Path(out).absolute()
    if source.suffix.lower() != '.pcbdoc' or not source.is_file():
        raise ValueError('Select the actual .PcbDoc, not its .PrjPcb project')
    before = digest(source)
    out.mkdir(parents=True, exist_ok=False)
    snapshot = out / 'Source.PcbDoc'
    shutil.copy2(source, snapshot)
    if digest(snapshot) != before or digest(source) != before:
        raise RuntimeError('PCB changed while snapshotting; retry after save completes')
    report, target = out / 'import_report.json', out / 'Board.kicad_pcb'
    command = [str(cli), 'pcb', 'import', '--format', 'altium', '--report-format', 'json',
               '--report-file', str(report), '--output', str(target), str(snapshot)]
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf8', errors='replace')
    (out / 'import.log').write_text(result.stdout + result.stderr, encoding='utf8')
    if result.returncode or not target.is_file():
        raise RuntimeError('KiCad import failed; inspect import.log')
    data = json.loads(report.read_text(encoding='utf-8-sig'))
    if data.get('errors'):
        raise RuntimeError('KiCad reported import errors: ' + str(data['errors']))
    if digest(source) != before:
        raise RuntimeError('Source changed during import')
    manifest = {'source': str(source), 'sha256': before, 'bytes': source.stat().st_size,
                'mtime': source.stat().st_mtime, 'imported': target.name,
                'warnings': data.get('warnings', []), 'command': command}
    (out / 'input.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    print(json.dumps(manifest, indent=2))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--kicad-cli', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.kicad_cli, args.out)
