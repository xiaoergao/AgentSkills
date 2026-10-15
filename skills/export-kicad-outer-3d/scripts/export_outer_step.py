"""Export selected external PCB graphics; never enable inner copper implicitly."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def digest(path):
    with Path(path).open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def run(pcb, cli, python, out, origin, hide_vias=False, soldermask=False, zones=False):
    pcb, out = Path(pcb).resolve(), Path(out).absolute()
    before = digest(pcb)
    out.mkdir(parents=True, exist_ok=False)
    source = pcb
    if hide_vias:
        source = out / 'NoVias.kicad_pcb'
        command = [str(python), str(Path(__file__).with_name('hide_vias.py')), str(pcb), str(source)]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf8', errors='replace')
        (out / 'hide_vias.log').write_text(result.stdout + result.stderr, encoding='utf8')
        if result.returncode or not source.is_file():
            raise RuntimeError('Export-copy preparation failed')
    target = out / 'Export.step'
    command = [str(cli), 'pcb', 'export', 'step', '--include-tracks', '--include-pads', '--include-silkscreen',
               '--user-origin', origin, '--output', str(target)]
    if soldermask:
        command.append('--include-soldermask')
    if zones:
        command.append('--include-zones')
    command.append(str(source))
    result = subprocess.run(command, capture_output=True, text=True, encoding='utf8', errors='replace')
    (out / 'export.log').write_text(result.stdout + result.stderr, encoding='utf8')
    if result.returncode or not target.is_file():
        raise RuntimeError('STEP export failed; inspect export.log')
    if digest(pcb) != before:
        raise RuntimeError('Source PCB changed')
    manifest = {'source_sha256': before, 'step_bytes': target.stat().st_size, 'hide_vias': hide_vias,
                'soldermask_geometry': soldermask, 'opacity_applied': False, 'inner_copper': False, 'command': command}
    (out / 'export.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    print(json.dumps(manifest, indent=2))
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('pcb', 'kicad-cli', 'kicad-python', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--origin', required=True)
    parser.add_argument('--hide-vias', action='store_true')
    parser.add_argument('--soldermask', action='store_true')
    parser.add_argument('--zones', action='store_true')
    args = parser.parse_args()
    run(args.pcb, args.kicad_cli, args.kicad_python, args.out, args.origin, args.hide_vias, args.soldermask, args.zones)
