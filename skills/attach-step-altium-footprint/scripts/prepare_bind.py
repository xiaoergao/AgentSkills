"""Prepare a copy and native Altium script; no application is started implicitly."""
import argparse,json,shutil
import struct
from pathlib import Path
from pcb_data import sha256
from merge_models import read,body_records
from compact_models import write_ole


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def run(library, footprint, recipe, out):
    library,recipe,out=library.resolve(),recipe.resolve(),out.absolute()
    out_text=str(out)
    if not out_text.isascii():
        raise ValueError('Use an ASCII output path for DelphiScript compatibility')
    config=json.loads(recipe.read_text(encoding='utf8'))
    bodies=config['bodies']
    if not bodies or len({Path(b['file']).name for b in bodies})!=len(bodies):
        raise ValueError('Nonempty recipe with unique model filenames required')
    for body in bodies:
        if not 0<=float(body['opacity'])<=1:raise ValueError('Invalid opacity')
        if not (recipe.parent/body['file']).is_file():raise ValueError('Missing STEP')
    out.mkdir(parents=True,exist_ok=False)
    shutil.copy2(library,out/'Original.PcbLib')
    streams,clsids,storages=read(library)
    key=(footprint,'Data');data=streams[key];prior=body_records(data,{Path(b['file']).name for b in bodies})
    chunks=[];last=0
    for start,end,record,model_name in prior:chunks.append(data[last:start]);last=end
    chunks.append(data[last:]);streams[key]=b''.join(chunks)
    count=struct.unpack('<I',streams[(footprint,'Header')])[0]
    streams[(footprint,'Header')]=struct.pack('<I',count-len(prior))
    write_ole(out/'Working.PcbLib',streams,clsids,storages)
    for body in bodies:shutil.copy2(recipe.parent/body['file'],out/Path(body['file']).name)
    script=r'''Var Log:TStringList;L:IPCB_Library;F:IPCB_LibComponent;
Procedure Stage(S:String);
Begin Log.Add(S);Log.SaveToFile(LOGFILE);End;
Procedure Bind(FileName:String;Opacity:Double;Color:Integer);
Var B:IPCB_ComponentBody;M:IPCB_Model;
Begin
 B:=PCBServer.PCBObjectFactory(eComponentBodyObject,eNoDimension,eCreate_Default);
 M:=B.ModelFactory_FromFilename(MODELDIR+FileName,False);
 If M=Nil Then RaiseException('Cannot load '+FileName);
 B.SetState_FromModel;B.Model:=M;B.Layer:=eMechanical13;B.BodyOpacity3D:=Opacity;
 If Color>=0 Then Begin B.OverrideColor:=True;B.BodyColor3D:=Color;End;
 B.MoveByXY(F.X,F.Y);L.Board.AddPCBObject(B);F.AddPCBObject(B);
 PCBServer.SendMessageToRobots(F.I_ObjectAddress,c_Broadcast,PCBM_BoardRegisteration,B.I_ObjectAddress);
 Stage('BOUND '+FileName);
End;
Procedure BindModels;
Var D:IServerDocument;I:Integer;T:IPCB_LibComponent;
Begin
 Log:=TStringList.Create;
 Try Stage('START');D:=Client.OpenDocument('PCBLIB',WORKFILE);Client.ShowDocument(D);L:=PCBServer.GetCurrentPCBLibrary;F:=Nil;
 For I:=0 To L.ComponentCount-1 Do Begin T:=L.GetComponent(I);If T.Name=FOOTPRINT Then F:=T;End;
 If F=Nil Then Begin Stage('TARGET_NOT_FOUND');Exit;End;
 L.SetState_CurrentComponent(F);PCBServer.PreProcess;
 Try
 BINDCALLS
 Finally PCBServer.PostProcess;End;
 D.SetFileName(OUTFILE);If D.DoFileSave('') Then Stage('SAVED') Else Stage('SAVE_FAILED');
 Finally Log.Free;End;
End;
'''
    calls=[]
    for body in bodies:
        color=body.get('color_bgr');color=-1 if color is None else int(color)
        calls.append(f"Bind({literal(Path(body['file']).name)},{float(body['opacity'])},{color});")
    for key,value in {'LOGFILE':literal(out/'bind.log'),'MODELDIR':literal(str(out)+'\\'),
            'WORKFILE':literal(out/'Working.PcbLib'),'FOOTPRINT':literal(footprint),
            'OUTFILE':literal(out/'Authored.PcbLib'),'BINDCALLS':'\n'.join(calls)}.items():
        script=script.replace(key,value)
    (out/'BindModels.pas').write_text(script,encoding='ascii')
    (out/'BindModels.PrjScr').write_text('[Design]\nVersion=1.0\n[Document1]\nDocumentPath=BindModels.pas\nAnnotationEnabled=0\n',encoding='ascii')
    command=f'"<Altium X2.exe>" "-RScriptingSystem:RunScript(ProjectName={out / "BindModels.PrjScr"}|ProcName=BindModels)"'
    (out/'run-command.txt').write_text(command,encoding='ascii')
    (out/'input.json').write_text(json.dumps({'library':str(library),'sha256':sha256(library),'footprint':footprint,'bodies':bodies},indent=2),encoding='utf8')
    print(command)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('library','recipe','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--footprint',required=True)
    a=p.parse_args();run(a.library,a.footprint,a.recipe,a.out)
