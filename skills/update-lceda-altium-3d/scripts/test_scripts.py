"""Synthetic geometry/CFB regression checks; no Altium process or user files modified."""
import contextlib
import io
import json
from pathlib import Path
import struct
import tempfile
import unittest
import uuid
from compact_models import compact, packblocks, write_ole
from inspect_pcb import inspect
from pcb_data import blocks, millimetres, sha256


class ParameterTests(unittest.TestCase):
    def test_units_and_truncated_blocks(self):
        self.assertAlmostEqual(millimetres(' -1.25e2mil '), -3.175)
        self.assertAlmostEqual(millimetres('1.6mm'), 1.6)
        with self.assertRaises(ValueError):
            millimetres('1.6')
        with self.assertRaises(ValueError):
            blocks(b'\x09\0\0\0short')


class CompactTests(unittest.TestCase):
    def fixture(self, path, different=False):
        first, second = ('{' + str(uuid.uuid4()).upper() + '}' for _ in range(2))
        rows = [('EMBED=TRUE|ID=%s|NAME=shared.step\0' % identity).encode() for identity in (first, second)]
        bodies = (('MODELID=%s|MODEL.3D.ROTX=0|MODEL.3D.ROTZ=90|MODEL.3D.DZ=0mil\0' % first) +
                  ('MODELID=%s|MODEL.3D.ROTX=180|MODEL.3D.ROTZ=225|MODEL.3D.DZ=-63mil\0' % second)).encode()
        streams = {('Models', 'Header'): struct.pack('<I', 2), ('Models', 'Data'): packblocks(rows),
                   ('Models', '0'): b'opaque STEP payload', ('Models', '1'): b'different' if different else b'opaque STEP payload',
                   ('ComponentBodies6', 'Header'): struct.pack('<I', 2), ('ComponentBodies6', 'Data'): bodies,
                   ('Tracks6', 'Data'): bytes(range(256)) * 40, ('Unrelated', 'Small'): b'preserve me'}
        write_ole(path, streams)
        return bodies, first, second

    def test_shared_geometry_preserves_instance_transforms_and_other_streams(self):
        import olefile
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp) / 'source.PcbDoc', Path(temp) / 'target.PcbDoc'
            bodies, first, second = self.fixture(source)
            before = sha256(source)
            with contextlib.redirect_stdout(io.StringIO()):
                report = compact(source, target)
            self.assertEqual(sha256(source), before)
            self.assertEqual(report['unique_embedded_models'], 1)
            with olefile.OleFileIO(str(source)) as a, olefile.OleFileIO(str(target)) as b:
                self.assertEqual(b.openstream('ComponentBodies6/Data').read(), bodies.replace(second.encode(), first.encode()))
                for name in ('Tracks6/Data', 'Unrelated/Small', 'ComponentBodies6/Header'):
                    self.assertEqual(a.openstream(name).read(), b.openstream(name).read())
            with self.assertRaises(ValueError):
                compact(source, source)
            with self.assertRaises(ValueError):
                compact(source, target)

    def test_conflicting_geometry_is_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as temp:
            source, target = Path(temp) / 'source.PcbDoc', Path(temp) / 'target.PcbDoc'
            self.fixture(source, different=True)
            before = sha256(source)
            with self.assertRaisesRegex(ValueError, 'different geometry'):
                compact(source, target)
            self.assertFalse(target.exists())
            self.assertEqual(sha256(source), before)


class GeometryTests(unittest.TestCase):
    def test_canonical_top_and_bottom_models_and_missing_model_stop(self):
        import math
        from prepare_models import prepare
        from xcaf_models import (new_document, write, load, bbox, gp_Trsf, gp_Vec, gp_Ax1, gp_Pnt, gp_Dir,
                                 TDataStd_Name, TCollection_ExtendedString, TopLoc_Location)
        from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
        from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
        from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
        from OCP.XCAFDoc import XCAFDoc_ColorGen
        with tempfile.TemporaryDirectory(prefix='cad_skill_') as temp:
            root = Path(temp)
            # Nonzero source origin and both PCB faces; P shares a model across faces,
            # Q has only a bottom representative and exercises inverse bottom normalization.
            parts = [('A1', 'P', 'TOP', 101, 81, 90), ('A2', 'P', 'BOTTOM', 110, 95, 225), ('B1', 'Q', 'BOTTOM', 95, 72, 90)]
            pcb, step, plan = root / 'board.PcbDoc', root / 'assembly.step', root / 'plan.json'
            pcb.write_text('\n'.join('|RECORD=Component|SOURCEDESIGNATOR=%s|PATTERN=%s|LAYER=%s|X=%gmm|Y=%gmm|ROTATION=%g|' % p for p in parts), encoding='ascii')
            data = {'source_origin_xy_mm': [100, 50], 'source_bottom_z_mm': 0,
                    'source_top_z_mm': 1.6, 'target_board_thickness_mm': 1.8}
            plan.write_text(json.dumps(data), encoding='utf8')
            doc, shapes, colors = new_document()
            assembly = shapes.NewShape()
            shape = BRepPrimAPI_MakeBox(gp_Pnt(-1, -.4, 0), 2, .8, .7).Shape()
            for ref, pattern, layer, x, y, angle in parts:
                tr = gp_Trsf()
                tr.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 0, 1)), math.radians(angle))
                if layer == 'BOTTOM':
                    flip = gp_Trsf()
                    flip.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0)), math.pi)
                    tr.Multiply(flip)
                shift = gp_Trsf()
                shift.SetTranslation(gp_Vec(x - 100, y - 50, 1.6 if layer == 'TOP' else 0))
                shift.Multiply(tr)
                item = shapes.AddShape(BRepBuilderAPI_Transform(shape, shift, True).Shape(), False)
                colors.SetColor(item, Quantity_Color(.7, .1, .2, Quantity_TOC_RGB), XCAFDoc_ColorGen)
                child = shapes.AddComponent(assembly, item, TopLoc_Location())
                TDataStd_Name.Set_s(child, TCollection_ExtendedString(ref))
            shapes.UpdateAssemblies()
            write(assembly, step)
            before = sha256(pcb)
            with contextlib.redirect_stdout(io.StringIO()):
                manifest = prepare(pcb, step, plan, root / 'prepared')
            self.assertEqual(len(manifest['models']), 2)
            self.assertEqual(sum(len(m['instances']) for m in manifest['models']), 3)
            for model in manifest['models']:
                doc2, st2, ct2, label2 = load(root / 'prepared' / model['file'])
                expected = [-1, -.4, 0, 1, .4, .7]
                for actual, wanted in zip(bbox(st2.GetShape_s(label2)), expected):
                    self.assertAlmostEqual(actual, wanted, places=5)
                for instance in model['instances']:
                    if instance['layer'] == 'BOTTOM':
                        self.assertEqual(instance['model_dz_mm'], -1.8)
                        self.assertEqual(instance['model_rx_deg'], 180)
            self.assertEqual(sha256(pcb), before)
            self.assertEqual(len(inspect(pcb)['components']), 3)
            with self.assertRaises(FileExistsError):
                prepare(pcb, step, plan, root / 'prepared')
            # A missing footprint must not receive a fabricated whole-board model.
            pcb.write_text(pcb.read_text() + '\n|RECORD=Component|SOURCEDESIGNATOR=M1|PATTERN=MISSING|LAYER=TOP|X=100mm|Y=80mm|ROTATION=0|')
            with self.assertRaisesRegex(ValueError, 'Missing STEP'):
                prepare(pcb, step, plan, root / 'missing')
            self.assertIn('MISSING', json.loads((root / 'missing/missing_models.json').read_text()))


if __name__ == '__main__':
    unittest.main()
