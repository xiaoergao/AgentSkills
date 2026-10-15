"""Normalize official KiCad straight dual-row models using registered pins 1/2/3.

Scope: male pins (1:0,0; 2:+pitch,0; 3:0,-pitch), female pins
(1:0,0; 2:-pitch,0; 3:0,-pitch). Verify a different model before use.
"""
import argparse
import json
import math
from pathlib import Path
from xcaf_models import (load, new_document, clone, bbox, write, gp_Trsf, TDataStd_Name, TCollection_ExtendedString)


def run(plan_file, male, female, out):
    plan = json.loads(plan_file.read_text(encoding='utf8'))
    pins = plan['connectors'][0]['pins_local_xy_up_mm']
    anchor = pins['1']
    u = [pins['2'][i] - anchor[i] for i in (0, 1)]
    v = [pins['3'][i] - anchor[i] for i in (0, 1)]
    pitch_u, pitch_v = math.hypot(*u), math.hypot(*v)
    if min(pitch_u, pitch_v) <= 0 or abs(sum(a*b for a, b in zip(u, v))) > 1e-4:
        raise ValueError('Orthogonal dual-row pin axes required')
    out.mkdir(parents=True, exist_ok=False)
    outputs = []
    for role, source, sign in [('MaleDown', male, 1), ('FemaleUp', female, -1)]:
        x = [sign * a/pitch_u for a in u]
        y = [-a/pitch_v for a in v]
        z = x[0]*y[1] - x[1]*y[0]
        if (role == 'MaleDown' and z > 0) or (role == 'FemaleUp' and z < 0):
            raise ValueError('Unexpected pin order/facing; inspect model axes')
        tr = gp_Trsf()
        tr.SetValues(x[0], y[0], 0, anchor[0], x[1], y[1], 0, anchor[1], 0, 0, z, 0)
        doc, shapes, colors, root = load(source)
        dest, ds, dc = new_document()
        assembly = ds.NewShape()
        TDataStd_Name.Set_s(assembly, TCollection_ExtendedString(role))
        clone(shapes, colors, root, tr, ds, dc, assembly, role)
        ds.UpdateAssemblies()
        path = out / (role + '.step')
        write(assembly, path)
        outputs.append({'role': role, 'file': str(path), 'bbox_mm': bbox(ds.GetShape_s(assembly))})
    (out / 'normalized.json').write_text(json.dumps(outputs, indent=2), encoding='utf8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('plan', 'male', 'female', 'out'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    run(args.plan, args.male, args.female, args.out)
