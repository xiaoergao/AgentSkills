"""Colored STEP helpers, tested with cadquery-ocp 8.x (not the unrelated ocp package)."""
from OCP.TDocStd import TDocStd_Document
from OCP.TCollection import TCollection_ExtendedString
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.XCAFDoc import XCAFDoc_DocumentTool, XCAFDoc_ColorGen, XCAFDoc_ColorSurf
from OCP.collections import Sequence_TDF_Label
from OCP.TDF import TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.Bnd import Bnd_Box
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
from OCP.TopLoc import TopLoc_Location
from OCP.TopExp import TopExp_Explorer
from OCP.TopAbs import TopAbs_FACE
from OCP.gp import gp_Trsf, gp_Vec, gp_Pnt, gp_Ax1, gp_Dir
from OCP.Quantity import Quantity_Color
from OCP.Interface import Interface_Static


def new_document():
    doc = TDocStd_Document(TCollection_ExtendedString('MDTV-XCAF'))
    return doc, XCAFDoc_DocumentTool.ShapeTool_s(doc.Main()), XCAFDoc_DocumentTool.ColorTool_s(doc.Main())


def load(path):
    doc, shapes, colors = new_document()
    reader = STEPCAFControl_Reader()
    reader.SetNameMode(True)
    reader.SetColorMode(True)
    if not str(reader.ReadFile(str(path))).endswith('RetDone') or not reader.Transfer(doc):
        raise ValueError('Cannot load STEP: ' + str(path))
    labels = Sequence_TDF_Label()
    shapes.GetFreeShapes(labels)
    if labels.Length() != 1:
        raise ValueError('Expected one STEP assembly root; found ' + str(labels.Length()))
    return doc, shapes, colors, labels.Value(1)


def name(label):
    attr = TDataStd_Name()
    return attr.Get().ToExtString() if label.FindAttribute(TDataStd_Name.GetID_s(), attr) else ''


def children(shapes, label):
    labels = Sequence_TDF_Label()
    shapes.GetComponents_s(label, labels)
    return [labels.Value(i) for i in range(1, labels.Length() + 1)]


def bbox(shape):
    box = Bnd_Box()
    BRepBndLib.Add_s(shape, box)
    low, high = box.CornerMin(), box.CornerMax()
    return [low.X(), low.Y(), low.Z(), high.X(), high.Y(), high.Z()]


def clone(shapes, colors, label, transform, dest_shapes, dest_colors, parent, title, inherited=None):
    if shapes.IsReference_s(label):
        target = TDF_Label()
        shapes.GetReferredShape_s(label, target)
        tr = transform.Multiplied(shapes.GetLocation_s(label).Transformation())
        return clone(shapes, colors, target, tr, dest_shapes, dest_colors, parent, title, inherited)
    for kind in (XCAFDoc_ColorSurf, XCAFDoc_ColorGen):
        color = Quantity_Color()
        if colors.GetColor_s(label, kind, color):
            inherited = color
            break
    if shapes.IsAssembly_s(label):
        for i, child in enumerate(children(shapes, label)):
            clone(shapes, colors, child, transform, dest_shapes, dest_colors, parent, title + '_' + str(i), inherited)
        return
    source = shapes.GetShape_s(label)
    if source.IsNull():
        return
    operation = BRepBuilderAPI_Transform(source, transform, True)
    item = dest_shapes.AddShape(operation.Shape(), False)
    TDataStd_Name.Set_s(item, TCollection_ExtendedString(title))
    dest_shapes.AddComponent(parent, item, TopLoc_Location())
    if inherited:
        dest_colors.SetColor(item, inherited, XCAFDoc_ColorGen)
    faces = TopExp_Explorer(source, TopAbs_FACE)
    while faces.More():
        face, color = faces.Current(), Quantity_Color()
        for kind in (XCAFDoc_ColorSurf, XCAFDoc_ColorGen):
            if colors.GetColor(face, kind, color):
                result = operation.ModifiedShape(face)
                if not result.IsNull():
                    dest_colors.SetColor(dest_shapes.AddSubShape(item, result), color, kind)
                break
        faces.Next()


def write(label, path):
    writer = STEPCAFControl_Writer()
    writer.SetColorMode(True)
    writer.SetNameMode(True)
    if not Interface_Static.SetIVal_s('write.surfacecurve.mode', 0):
        raise RuntimeError('Unsupported STEP writer option')
    if not writer.Transfer(label) or not str(writer.Write(str(path))).endswith('RetDone'):
        raise RuntimeError('STEP export failed: ' + str(path))
