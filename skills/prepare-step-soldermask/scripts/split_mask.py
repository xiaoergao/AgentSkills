"""Split named KiCad XCAF geometry; opacity is a binding recipe, not STEP alpha."""
import argparse, json
from pathlib import Path
from xcaf_models import load, children, name, bbox, write, TDataStd_Name, TCollection_ExtendedString, gp_Trsf, gp_Vec, TopLoc_Location, TDF_Label


def referred(shapes, label):
    if shapes.IsReference_s(label):
        result = TDF_Label()
        shapes.GetReferredShape_s(label, result)
        return result
    return label


def run(source, out, lift, opacity):
    if not 0 <= opacity <= 1:
        raise ValueError('Opacity must be in [0, 1]')
    out.mkdir(parents=True, exist_ok=False)
    doc, shapes, colors, root = load(source)
    roots = {key: shapes.NewShape() for key in ('Main', 'Soldermask')}
    entries = []
    for key, label in roots.items():
        TDataStd_Name.Set_s(label, TCollection_ExtendedString(key))
    for label in children(shapes, root):
        definition = referred(shapes, label)
        title = name(label) + ' ' + name(definition)
        kind = 'Soldermask' if 'soldermask' in title.lower() else 'Main'
        shapes.AddComponent(roots[kind], definition, shapes.GetLocation_s(label))
        entries.append({'instance': name(label), 'product': name(definition), 'kind': kind,
                        'bbox_mm': bbox(shapes.GetShape_s(label))})
    if sum(x['kind'] == 'Soldermask' for x in entries) < 2:
        raise ValueError('Cannot identify top and bottom mask geometry; inspect names')
    models = []
    for kind, label in roots.items():
        mounted = shapes.NewShape()
        TDataStd_Name.Set_s(mounted, TCollection_ExtendedString(kind + '_Mounted'))
        transform = gp_Trsf()
        transform.SetTranslation(gp_Vec(0, 0, lift))
        shapes.AddComponent(mounted, label, TopLoc_Location(transform))
        shapes.UpdateAssemblies()
        target = out / (kind + '.step')
        write(mounted, target)
        models.append({'file': target.name, 'opacity': opacity if kind == 'Soldermask' else 1.0,
                       'color_bgr': 0x295912 if kind == 'Soldermask' else None,
                       'bytes': target.stat().st_size, 'bbox_mm': bbox(shapes.GetShape_s(mounted))})
    report = {'source': str(source.resolve()), 'z_lift_mm': lift, 'geometry': entries, 'bodies': models}
    (out / 'bodies.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(models))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--step', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--z-lift-mm', type=float, required=True)
    parser.add_argument('--opacity', type=float, default=.7)
    args = parser.parse_args()
    run(args.step, args.out, args.z_lift_mm, args.opacity)
