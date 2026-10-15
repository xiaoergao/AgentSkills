"""Merge one native-authored symbol; preserve other symbols and global font table."""
import argparse,json,re,struct
from pathlib import Path
import olefile
from compact_models import write_ole
from pcb_data import sha256


def records(data):
    i=0;result=[]
    while i<len(data):
        n=struct.unpack_from('<I',data,i)[0];length=n&0xffffff
        result.append((n>>24,data[i+4:i+4+length]));i+=length+4
    if i!=len(data):raise ValueError('Invalid record boundary')
    return result


def run(original,authored,name,pins,out):
    if out.exists() or out.resolve() in (original.resolve(),authored.resolve()):raise ValueError('New output required')
    with olefile.OleFileIO(str(original)) as f:
        old={tuple(p):f.openstream(p).read() for p in f.listdir()};streams=old.copy()
        clsids={tuple(f.getpath(i)) if i else ():d.clsid for i,d in enumerate(f.direntries) if d and d.entry_type in (1,5) and d.clsid}
        storages=[tuple(p) for p in f.listdir(streams=False,storages=True)]
    key=(name,'Data')
    if key not in old:raise ValueError('Named draft absent from original library')
    with olefile.OleFileIO(str(authored)) as f:
        if [p for p in f.listdir() if p[0]==name]!=[[name,'Data']]:raise ValueError('Additional symbol auxiliary streams need explicit compatibility handling')
        streams[key]=f.openstream(key).read()
    got=[]
    for flag,body in records(streams[key]):
        if flag!=1:continue
        if len(body)<27 or struct.unpack_from('<I',body)[0]!=2:raise ValueError('Unsupported binary symbol record')
        pos=26;n=body[pos];text=body[pos+1:pos+1+n].decode('utf8');pos+=n+1;n=body[pos];number=body[pos+1:pos+1+n].decode('ascii');got.append((number,text))
    expected=json.loads(pins.read_text(encoding='utf8'))['pins']
    if len(got)!=len(expected) or dict(got)!={r['pin']:r['name'] for r in expected}:raise ValueError('Saved pin Names or Designators differ')
    header=old[('FileHeader',)][4:]
    matched=[m for m in re.finditer(rb'\|LIBREF(\d+)=([^|\x00]+)',header,re.I) if m[2]==name.encode('utf8')]
    if len(matched)!=1:raise ValueError('Ambiguous global component index')
    count=re.search(rb'\|PARTCOUNT=(\d+)',streams[key],re.I)[1]
    pattern=rb'(\|PARTCOUNT'+matched[0][1]+rb'=)\d+'
    header=re.sub(pattern,lambda m:m[1]+count,header,flags=re.I)
    delta=len(records(streams[key]))-len(records(old[key]))
    header=re.sub(rb'(\|WEIGHT=)(\d+)',lambda m:m[1]+str(int(m[2])+delta).encode(),header,flags=re.I)
    streams[('FileHeader',)]=struct.pack('<I',len(header))+header
    for k,v in old.items():
        if k not in (key,('FileHeader',)) and streams[k]!=v:raise RuntimeError('Unrelated symbol changed')
    write_ole(out,streams,clsids,storages)
    with olefile.OleFileIO(str(out)) as f:
        for k,v in streams.items():
            if f.openstream(k).read()!=v:raise RuntimeError('Written stream mismatch')
    report={'original_sha256':sha256(original),'new_sha256':sha256(out),'pins':len(got),'other_symbols_unchanged':True,'full_names_verified':True}
    out.with_suffix('.validation.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('original','authored','pins','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--name',required=True);a=p.parse_args();run(a.original,a.authored,a.name,a.pins,a.out)
