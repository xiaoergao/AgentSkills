"""Run with KiCad pcbnew Python. Separate registration and assembly actions."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics
import pcbnew as pcb


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def register(source, library, footprint, mappings, output):
    if output.exists():
        raise ValueError('Output exists')
    before = [digest(source), digest(library)]
    board = pcb.LoadBoard(str(source))
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    lib = pcb.PCB_IO_MGR.FindPlugin(pcb.PCB_IO_MGR.ALTIUM_DESIGNER).FootprintLoad(str(library), footprint)
    pads = {}
    for pad in lib.Pads():
        number = pad.GetNumber()
        if number == '0':
            continue  # Common mechanical-hole placeholder; not mapped signal pins.
        if number in pads:
            raise ValueError('Duplicate target signal pad number: ' + number)
        pads[number] = pad
    differences, connectors = [], []
    for mapping in mappings:
        ref, offset = mapping.rsplit(':', 1)
        offset, fp = int(offset), fps[ref]
        source_pads = {pad.GetNumber(): pad for pad in fp.Pads()}
        for number, pad in source_pads.items():
            target = pads[str(int(number) + offset)]
            a, b = pcb.ToMM(pad.GetPosition()), pcb.ToMM(target.GetPosition())
            differences.append([a[i] - b[i] for i in (0, 1)])
            if abs(pcb.ToMM(pad.GetDrillSize().x) - pcb.ToMM(target.GetDrillSize().x)) > .001:
                raise ValueError('Drill mismatch: ' + mapping + '.' + number)
        center = list(pcb.ToMM(fp.GetPosition()))
        local = {}
        for number in ('1', '2', '3'):
            a = pcb.ToMM(source_pads[number].GetPosition())
            local[number] = [a[0] - center[0], -(a[1] - center[1])]
        connectors.append({'reference': ref, 'pad_offset': offset, 'position_mm': center, 'pins_local_xy_up_mm': local})
    origin = [statistics.median(d[i] for d in differences) for i in (0, 1)]
    error = max(math.dist(d, origin) for d in differences)
    if error > .001:
        raise ValueError('Not a common translation; maximum error mm=' + str(error))
    first = connectors[0]['pins_local_xy_up_mm']
    for c in connectors:
        if any(math.dist(c['pins_local_xy_up_mm'][n], first[n]) > .001 for n in first):
            raise ValueError('Connector local axes differ; shared canonical model needs explicit rotations')
    result = {'pcb': str(source.resolve()), 'pcb_sha256': before[0], 'library_sha256': before[1],
              'footprint': footprint, 'origin_in_kicad_mm': origin, 'maximum_pad_error_mm': error,
              'pads_checked': len(differences), 'connectors': connectors}
    if [digest(source), digest(library)] != before:
        raise RuntimeError('Input changed')
    output.write_text(json.dumps(result, indent=2), encoding='utf8')
    print(json.dumps(result, indent=2))


def assemble(plan_file, male, female, male_height, female_height, output):
    if output.exists() or male_height <= 0 or female_height <= 0:
        raise ValueError('New output and positive selected housing heights required')
    plan = json.loads(plan_file.read_text(encoding='utf8'))
    source = Path(plan['pcb'])
    if digest(source) != plan['pcb_sha256']:
        raise RuntimeError('Registered PCB changed; repeat registration')
    board = pcb.LoadBoard(str(source))
    thickness = pcb.ToMM(board.GetDesignSettings().GetBoardThickness())
    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    for connector in plan['connectors']:
        comp = fps[connector['reference']]
        comp.Models().clear()
        for role, path, dz in [('MALE', male, -thickness), ('FEMALE', female, -thickness - male_height - female_height)]:
            carrier = pcb.FOOTPRINT(board)
            carrier.SetReference('VIS_' + comp.GetReference() + '_' + role)
            carrier.SetPosition(comp.GetPosition())
            carrier.SetLayer(pcb.F_Cu)
            carrier.Reference().SetVisible(False)
            carrier.Value().SetVisible(False)
            model = pcb.FP_3DMODEL()
            model.m_Filename = str(path.resolve())
            model.m_Offset.z = dz
            carrier.Models().append(model)
            board.Add(carrier)
    pcb.SaveBoard(str(output), board)
    if digest(source) != plan['pcb_sha256']:
        raise RuntimeError('Source changed')
    output.with_suffix('.assembly.json').write_text(json.dumps({'board_thickness_mm': thickness,
        'nominal_board_spacing_mm': male_height + female_height, 'male_housing_mm': male_height,
        'female_housing_mm': female_height, 'original_pads_preserved': len(list(board.GetPads()))}, indent=2), encoding='utf8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest='action', required=True)
    a = actions.add_parser('register')
    for name in ('pcb', 'library', 'output'):
        a.add_argument('--' + name, type=Path, required=True)
    a.add_argument('--footprint', required=True)
    a.add_argument('--connector', action='append', required=True)
    a = actions.add_parser('assemble')
    for name in ('plan', 'male-model', 'female-model', 'output'):
        a.add_argument('--' + name, type=Path, required=True)
    for name in ('male-housing-mm', 'female-housing-mm'):
        a.add_argument('--' + name, type=float, required=True)
    args = parser.parse_args()
    if args.action == 'register':
        register(args.pcb, args.library, args.footprint, args.connector, args.output)
    else:
        assemble(args.plan, args.male_model, args.female_model, args.male_housing_mm, args.female_housing_mm, args.output)
