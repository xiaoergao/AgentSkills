"""Prepare shared colored STEP and an AD script; does not run AD or change inputs.

Scope: matching LCEDA Altium export + assembly with designator-named root children,
XY translation registration, Z-up source with known top/bottom mounting planes.
"""
import argparse
import collections
import json
import math
import shutil
from pathlib import Path
from pcb_data import read_pcb, millimetres, sha256


def literal(text):
    text.encode('ascii')  # AD18 DelphiScript code-page boundary: fail instead of corrupting.
    return text.replace("'", "''")


def prepare(pcb, step, plan_file, out):
    from xcaf_models import (load, children, name, new_document, clone, bbox, write,
                             gp_Trsf, gp_Vec, gp_Pnt, gp_Ax1, gp_Dir,
                             TDataStd_Name, TCollection_ExtendedString)
    pcb, step, plan_file = (Path(p).resolve() for p in (pcb, step, plan_file))
    out = Path(out).absolute()
    literal(str(out))
    plan = json.loads(plan_file.read_text(encoding='utf-8-sig'))
    origin_x, origin_y = map(float, plan['source_origin_xy_mm'])
    top_z, bottom_z = float(plan['source_top_z_mm']), float(plan['source_bottom_z_mm'])
    thickness = float(plan['target_board_thickness_mm'])
    if not all(math.isfinite(x) for x in (origin_x, origin_y, top_z, bottom_z, thickness)) or thickness <= 0 or top_z <= bottom_z:
        raise ValueError('Finite coordinates, positive target thickness and top > bottom required')
    data = read_pcb(pcb)
    excluded = set(plan.get('exclude_references', []))
    refs = {p['SOURCEDESIGNATOR'] for p in data['components']}
    if excluded - refs:
        raise ValueError('Unknown excluded references: ' + str(sorted(excluded - refs)))
    parts = [p for p in data['components'] if p['SOURCEDESIGNATOR'] not in excluded]
    groups = collections.defaultdict(list)
    for p in parts:
        literal(p['SOURCEDESIGNATOR'])
        groups[p['PATTERN']].append(p)
    overrides = {k: (plan_file.parent / v).resolve() for k, v in plan.get('canonical_models', {}).items()}
    if set(overrides) - set(groups):
        raise ValueError('Canonical model pattern not present in PCB')
    for path in overrides.values():
        if not path.is_file():
            raise FileNotFoundError(path)
    doc, shapes, colors, root = load(step)
    labels = {}
    for label in children(shapes, root):
        key = name(label)
        if key not in refs:
            continue  # Board/copper/silkscreen roots are not component models.
        if key in labels:
            raise ValueError('Duplicate STEP root-child label: ' + key)
        labels[key] = label
    missing = {k: [p['SOURCEDESIGNATOR'] for p in v]
               for k, v in groups.items() if k not in overrides and not any(p['SOURCEDESIGNATOR'] in labels for p in v)}
    out.mkdir(parents=True, exist_ok=False)
    if missing:
        (out / 'missing_models.json').write_text(json.dumps(missing, indent=2), encoding='utf8')
        raise ValueError('Missing STEP models; see ' + str(out / 'missing_models.json'))
    model_dir = out / 'Models'
    model_dir.mkdir()
    manifest = {'inputs': [{'file': str(p), 'sha256': sha256(p)} for p in (pcb, step, plan_file)],
                'registration': {k: plan[k] for k in ('source_origin_xy_mm', 'source_top_z_mm', 'source_bottom_z_mm', 'target_board_thickness_mm')},
                'excluded_references': sorted(excluded), 'models': []}
    calls = []
    for i, (pattern, instances) in enumerate(groups.items(), 1):
        filename = 'FP%03d.step' % i
        model_path = model_dir / filename
        representative = next((p for p in instances if p['LAYER'] == 'TOP' and p['SOURCEDESIGNATOR'] in labels),
                              next((p for p in instances if p['SOURCEDESIGNATOR'] in labels), instances[0]))
        if pattern in overrides:
            model_doc, model_shapes, model_colors, model_root = load(overrides[pattern])
            box = bbox(model_shapes.GetShape_s(model_root))
            shutil.copy2(overrides[pattern], model_path)
            source = {'canonical_override': str(overrides[pattern]), 'sha256': sha256(overrides[pattern])}
        else:
            p = representative
            shift = gp_Trsf()
            shift.SetTranslation(gp_Vec(-(millimetres(p['X']) - origin_x), -(millimetres(p['Y']) - origin_y),
                                       -(top_z if p['LAYER'] == 'TOP' else bottom_z)))
            rotate = gp_Trsf()
            rotate.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), -math.radians(float(p['ROTATION'])))
            rotate.Multiply(shift)
            if p['LAYER'] == 'BOTTOM':
                flip = gp_Trsf()
                flip.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0)), math.pi)
                flip.Multiply(rotate)
                rotate = flip
            model_doc, model_shapes, model_colors = new_document()
            model_root = model_shapes.NewShape()
            TDataStd_Name.Set_s(model_root, TCollection_ExtendedString(pattern))
            clone(shapes, colors, labels[p['SOURCEDESIGNATOR']], rotate, model_shapes, model_colors, model_root, pattern)
            model_shapes.UpdateAssemblies()
            box = bbox(model_shapes.GetShape_s(model_root))
            write(model_root, model_path)
            source = {'assembly_designator': p['SOURCEDESIGNATOR']}
        row = {'pattern': pattern, 'file': 'Models/' + filename, 'bbox_mm': box,
               'bytes': model_path.stat().st_size, 'sha256': sha256(model_path), 'source': source, 'instances': []}
        for p in instances:
            bottom = p['LAYER'] == 'BOTTOM'
            rx, rz, dz = (180 if bottom else 0), float(p['ROTATION']), (-thickness if bottom else 0)
            if not math.isfinite(rz):
                raise ValueError('Non-finite component rotation')
            calls.append(" Attach('%s','%s',%g,%g,%d);" % (literal(p['SOURCEDESIGNATOR']), filename, rx, rz, round(dz / .0254 * 10000)))
            row['instances'].append({'reference': p['SOURCEDESIGNATOR'], 'layer': p['LAYER'],
                                     'x_mm': millimetres(p['X']), 'y_mm': millimetres(p['Y']),
                                     'rotation_deg': rz, 'model_rx_deg': rx, 'model_rz_deg': rz, 'model_dz_mm': dz})
        manifest['models'].append(row)
        print('PREPARED', filename, len(instances), flush=True)
    shutil.copy2(pcb, out / 'Source.PcbDoc')
    template = Path(__file__).with_name('build_models.pas.in').read_text(encoding='ascii')
    substitutions = {'LOG': str(out / 'build.log'), 'SOURCE': str(out / 'Source.PcbDoc'),
                     'TARGET': str(out / 'Board3D_Raw.PcbDoc'), 'MODELS': str(model_dir),
                     'REPLACE': str(int(bool(plan.get('replace_existing_bodies', False))))}
    for key, value in substitutions.items():
        template = template.replace('@' + key + '@', literal(value))
    template = template.replace('@ATTACH@', '\n'.join(calls))
    (out / 'BuildModels.pas').write_text(template, encoding='ascii')
    (out / 'BuildModels.PrjScr').write_text('[Design]\nVersion=1.0\n[Document1]\nDocumentPath=BuildModels.pas\nAnnotationEnabled=0\n', encoding='ascii')
    command = 'X2.EXE "-RScriptingSystem:RunScript(ProjectName=%s|ProcName=BuildModels)"' % (out / 'BuildModels.PrjScr')
    (out / 'run-command.txt').write_text(command + '\n', encoding='ascii')
    (out / 'model_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf8')
    for item in manifest['inputs']:
        if sha256(item['file']) != item['sha256']:
            raise RuntimeError('Input changed during preparation: ' + item['file'])
    print('READY', len(parts), 'bodies;', len(groups), 'shared models. AD has not been run.')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('pcb', 'step', 'plan', 'out'):
        parser.add_argument('--' + key, type=Path, required=True)
    args = parser.parse_args()
    prepare(args.pcb, args.step, args.plan, args.out)
