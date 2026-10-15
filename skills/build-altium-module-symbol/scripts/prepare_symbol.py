"""Prepare native SchLib draft creation or name-only edits on a copy."""
import argparse,json,re,shutil
from pathlib import Path


def q(value):return "'"+str(value).replace("'","''")+"'"


def run(library,name,footprint,pins,mode,out):
    if not str(out.absolute()).isascii():raise ValueError('ASCII output path required')
    rows=json.loads(pins.read_text(encoding='utf8'))['pins']
    if len({r['pin'] for r in rows})!=len(rows):raise ValueError('Duplicate pin numbers')
    out=out.absolute();out.mkdir(parents=True,exist_ok=False);shutil.copy2(library,out/'Original.SchLib');shutil.copy2(library,out/'Working.SchLib')
    script='''Var Log:TStringList;Lib:ISch_Lib;C:ISch_Component;
Procedure Stage(S:String);
Begin Log.Add(S);Log.SaveToFile(LOGFILE);End;
Procedure Box(PartID,Width,Height:Integer;Title:String);
Var R:ISch_Rectangle;T:ISch_Label;
Begin
 R:=SchServer.SchObjectFactory(eRectangle,eCreate_Default);R.OwnerPartID:=PartID;R.OwnerPartDisplayMode:=0;
 R.Location:=Point(MilsToCoord(0),MilsToCoord(-Height));R.Corner:=Point(MilsToCoord(Width),0);R.LineWidth:=eSmall;R.Color:=128;R.AreaColor:=11599871;R.IsSolid:=True;C.AddSchObject(R);
 T:=SchServer.SchObjectFactory(eLabel,eCreate_Default);T.OwnerPartID:=PartID;T.OwnerPartDisplayMode:=0;T.Location:=Point(MilsToCoord(150),MilsToCoord(-150));T.Text:=Title;T.FontID:=1;T.Color:=128;C.AddSchObject(T);
End;
Procedure Pin(PartID:Integer;Number,PinName:String;Y,Electrical:Integer);
Var P:ISch_Pin;
Begin
 P:=SchServer.SchObjectFactory(ePin,eCreate_Default);P.OwnerPartID:=PartID;P.OwnerPartDisplayMode:=0;
 P.Location:=Point(0,MilsToCoord(Y));P.Orientation:=eRotate180;P.PinLength:=MilsToCoord(200);P.Designator:=Number;P.Name:=PinName;
 P.ShowName:=True;P.ShowDesignator:=True;P.IsHidden:=False;
 If Electrical=7 Then P.Electrical:=eElectricPower Else If Electrical=4 Then P.Electrical:=eElectricPassive Else P.Electrical:=eElectricIO;
 C.AddSchObject(P);
End;
Procedure UpdateSymbol;
Var D:IServerDocument;It:ISch_Iterator;Obj,Old:ISch_GraphicalObject;P:ISch_Pin;Imp:ISch_Implementation;I,N:Integer;Names:TStringList;
Begin
 Log:=TStringList.Create;Names:=TStringList.Create;
 Try Stage('START');D:=Client.OpenDocument('SCHLIB',WORKFILE);Client.ShowDocument(D);Lib:=SchServer.GetCurrentSchDocument;C:=Lib.GetState_SchComponentByLibRef(SYMBOLNAME);
 If C=Nil Then Begin Stage('MISSING_DRAFT');Exit;End;
 N:=0;It:=C.SchIterator_Create;It.AddFilter_ObjectSet(MkSet(ePin));
 Try Obj:=It.FirstSchObject;While Obj<>Nil Do Begin N:=N+1;Obj:=It.NextSchObject;End;Finally C.SchIterator_Destroy(It);End;
 ACTION
 D.SetFileName(OUTFILE);If D.DoFileSave('') Then Stage('SAVED') Else Stage('SAVE_FAILED');
 Finally Names.Free;Log.Free;End;
End;
'''
    if mode=='build':
        groups={}
        for r in rows:
            match=re.match(r'^(P[A-F])\d\d/',r['name']);groups.setdefault(match[1] if match else 'POWER_OTHER',[]).append(r)
        action=["If (N<>0) Or (C.PartCount<>1) Then Begin Stage('DRAFT_NOT_EMPTY');Exit;End;",
            "It:=C.SchIterator_Create;It.AddFilter_ObjectSet(MkSet(eRectangle));Try Obj:=It.FirstSchObject;While Obj<>Nil Do Begin Old:=Obj;Obj:=It.NextSchObject;C.RemoveSchObject(Old);End;Finally C.SchIterator_Destroy(It);End;",
            f'For I:=2 To {len(groups)} Do C.AddPart;',"C.CurrentPartID:=1;C.DisplayMode:=0;C.Designator.Text:='M?';C.Comment.Text:="+q(name)+';']
        for i,(key,rs) in enumerate(sorted(groups.items()),1):
            rs.sort(key=lambda r:r['name']);width=max(1800,((max(len(r['name']) for r in rs)*65+499)//500)*500)
            action.append(f'Box({i},{width},{len(rs)*200+400},{q(key)});')
            for j,r in enumerate(rs):
                electric=7 if r.get('is_supply') else 1 if re.match(r'^P[A-F]\d\d/',r['name']) else 4
                action.append(f'Pin({i},{q(r["pin"])},{q(r["name"])},{-300-j*200},{electric});')
        action.append('Imp:=C.AddSchImplementation;Imp.ModelName:='+q(footprint)+";Imp.ModelType:='PCBLIB';Imp.ClearAllDatafileLinks;Imp.AddDataFileLink("+q(footprint)+",'','PCBLib');Imp.IsCurrent:=True;")
    else:
        action=[f"If N<>{len(rows)} Then Begin Stage('PIN_COUNT_MISMATCH');Exit;End;"]
        for r in rows:action.append('Names.Values['+q(r['pin'])+']:='+q(r['name'])+';')
        action.append("It:=C.SchIterator_Create;It.AddFilter_ObjectSet(MkSet(ePin));Try P:=It.FirstSchObject;While P<>Nil Do Begin If Names.Values[P.Designator]='' Then RaiseException('Unexpected pin '+P.Designator);P.Name:=Names.Values[P.Designator];Names.Values[P.Designator]:='';P:=It.NextSchObject;End;Finally C.SchIterator_Destroy(It);End;")
    for key,value in {'LOGFILE':q(out/'symbol.log'),'WORKFILE':q(out/'Working.SchLib'),'SYMBOLNAME':q(name),'OUTFILE':q(out/'Authored.SchLib'),'ACTION':'\n'.join(action)}.items():script=script.replace(key,value)
    (out/'UpdateSymbol.pas').write_text(script,encoding='ascii');(out/'UpdateSymbol.PrjScr').write_text('[Design]\nVersion=1.0\n[Document1]\nDocumentPath=UpdateSymbol.pas\nAnnotationEnabled=0\n',encoding='ascii')
    (out/'run-command.txt').write_text('"<Altium X2.exe>" "-RScriptingSystem:RunScript(ProjectName='+str(out/'UpdateSymbol.PrjScr')+'|ProcName=UpdateSymbol)"',encoding='ascii')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('library','pins','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--name',required=True);p.add_argument('--footprint',required=True);p.add_argument('--mode',choices=['build','names'],required=True)
    a=p.parse_args();run(a.library,a.name,a.footprint,a.pins,a.mode,a.out)
