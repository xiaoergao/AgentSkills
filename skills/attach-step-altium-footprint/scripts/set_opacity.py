"""Change one named Body's fixed-width opacity; preserve all geometry streams."""
import argparse,re,json
from pathlib import Path
from merge_models import read,body_records
from compact_models import write_ole
from pcb_data import sha256


def run(source,footprint,model,opacity,out):
    if not 0<=opacity<=1 or out.exists() or out.resolve()==source.resolve():raise ValueError('New output and valid opacity required')
    old,clsids,storages=read(source);streams=old.copy();key=(footprint,'Data');matches=body_records(old[key],{model})
    if len(matches)!=1:raise ValueError('Expected exactly one matching body')
    start,end,record,_=matches[0];match=re.search(rb'(BODYOPACITY3D=)([01]\.\d{3})(\|)',record)
    if not match:raise ValueError('Unsupported opacity format; use native AD API')
    changed=record[:match.start(2)]+f'{opacity:.3f}'.encode()+record[match.end(2):]
    assert len(changed)==len(record)
    streams[key]=old[key][:start]+changed+old[key][end:]
    write_ole(out,streams,clsids,storages)
    check,_,_=read(out)
    assert check==streams and all(check[k]==v for k,v in old.items() if k!=key)
    print(json.dumps({'input_sha256':sha256(source),'output_sha256':sha256(out),'opacity':opacity,'geometry_unchanged':True}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('library','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--footprint',required=True);p.add_argument('--model-name',required=True);p.add_argument('--opacity',type=float,required=True)
    a=p.parse_args();run(a.library,a.footprint,a.model_name,a.opacity,a.out)
