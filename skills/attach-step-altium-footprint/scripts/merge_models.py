"""Merge native AD body records while preserving every other primitive byte."""
import argparse,json,re,struct
from pathlib import Path
import olefile
from compact_models import write_ole,packblocks
from pcb_data import blocks,parameters,sha256


def read(path):
    with olefile.OleFileIO(str(path)) as ole:
        streams={tuple(p):ole.openstream(p).read() for p in ole.listdir()}
        clsids={tuple(ole.getpath(i)) if i else ():d.clsid for i,d in enumerate(ole.direntries)
                if d and d.entry_type in (1,5) and d.clsid}
        storages=[tuple(p) for p in ole.listdir(streams=False,storages=True)]
    return streams,clsids,storages


def body_records(data,names):
    found=[]
    for pos,byte in enumerate(data):
        if byte!=12 or pos+5>len(data):continue
        size=struct.unpack_from('<I',data,pos+1)[0];end=pos+5+size
        if end>len(data) or size<60:continue
        record=data[pos:end]
        if b'V7_LAYER=' not in record[:180]:continue
        match=re.search(rb'\|MODEL.NAME=([^|]+)\|',record)
        if match and match[1].decode('utf8') in names:
            found.append((pos,end,record,match[1].decode('utf8')))
    if any(a[1]>b[0] for a,b in zip(found,found[1:])):raise ValueError('Overlapping body records')
    return found


def run(original,authored,footprint,recipe,out):
    if out.exists() or out.resolve() in (original.resolve(),authored.resolve()):raise ValueError('New output required')
    before=sha256(original);old,clsids,storages=read(original);native,_,_=read(authored);streams=old.copy()
    bodies=json.loads(recipe.read_text(encoding='utf8'))['bodies'];names={Path(b['file']).name for b in bodies}
    if len(names)!=len(bodies):raise ValueError('Duplicate model names')
    key=(footprint,'Data');prior=body_records(old[key],names);new=body_records(native[key],names)
    if len(new)!=len(names) or {r[3] for r in new}!=names:raise ValueError('Expected one native body per recipe model')
    chunks=[];last=0
    for start,end,record,name in prior:chunks.append(old[key][last:start]);last=end
    chunks.append(old[key][last:]);preserved=b''.join(chunks)
    streams[key]=preserved+b''.join(r[2] for r in new)
    oldcount=struct.unpack('<I',old[(footprint,'Header')])[0]
    streams[(footprint,'Header')]=struct.pack('<I',oldcount-len(prior)+len(new))
    removed_ids={re.search(rb'MODELID=(\{[^}]+\})',r[2])[1] for r in prior}
    used_ids=set()
    for k,v in streams.items():
        if k[-1]=='Data' and k!=('Library','Models','Data'):used_ids.update(re.findall(rb'MODELID=(\{[^}]+\})',v))
    modelrows=blocks(old[('Library','Models','Data')]);payloads=[]
    for i,row in enumerate(modelrows):
        identity=parameters(row)['ID'].encode()
        if identity in removed_ids and identity not in used_ids:continue
        payloads.append((row,old[('Library','Models',str(i))]))
    native_rows=blocks(native[('Library','Models','Data')]);details=[]
    for start,end,record,name in new:
        if b'MODEL.2D.X=0mil|' not in record or b'MODEL.2D.Y=0mil|' not in record:
            raise ValueError('Native model is offset relative to existing footprint origin')
        opacity=float(re.search(rb'BODYOPACITY3D=([^|]+)',record)[1]);expected=next(b['opacity'] for b in bodies if Path(b['file']).name==name)
        if abs(opacity-expected)>1e-5:raise ValueError('Native opacity differs from recipe')
        identity=re.search(rb'MODELID=(\{[^}]+\})',record)[1]
        matches=[(i,row) for i,row in enumerate(native_rows) if parameters(row)['ID'].encode()==identity]
        if len(matches)!=1:raise ValueError('Ambiguous native model ID')
        i,row=matches[0];payload=native[('Library','Models',str(i))]
        existing=[(r,p) for r,p in payloads if parameters(r)['ID'].encode()==identity]
        if existing:
            if len(existing)!=1 or existing[0][1]!=payload:raise ValueError('Same model ID has different payload')
        else:payloads.append((row,payload))
        details.append({'name':name,'opacity':opacity,'embedded_bytes':len(payload)})
    for k in list(streams):
        if len(k)==3 and k[:2]==('Library','Models') and k[2].isdigit():del streams[k]
    for i,(row,payload) in enumerate(payloads):streams[('Library','Models',str(i))]=payload
    streams[('Library','Models','Header')]=struct.pack('<I',len(payloads))
    streams[('Library','Models','Data')]=packblocks([x[0] for x in payloads])
    for k,v in old.items():
        allowed=k in (key,(footprint,'Header')) or k[:2]==('Library','Models')
        if not allowed and streams.get(k)!=v:raise RuntimeError('Unrelated library stream changed')
    if sha256(original)!=before:raise RuntimeError('Original library changed')
    write_ole(out,streams,clsids,storages)
    check,_,_=read(out)
    if check!=streams:raise RuntimeError('Written library does not match')
    report={'original_sha256':before,'new_sha256':sha256(out),'original_bytes':original.stat().st_size,'new_bytes':out.stat().st_size,
            'footprint':footprint,'old_primitive_count':oldcount,'new_primitive_count':oldcount-len(prior)+len(new),
            'model_count':len(payloads),'new_bodies':details,'all_unrelated_primitives_preserved':True}
    out.with_suffix('.validation.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('original','authored','recipe','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--footprint',required=True)
    a=p.parse_args();run(a.original,a.authored,a.footprint,a.recipe,a.out)
