"""LCEDA Pro MCU symbol names + verified connector netlist -> module pin map."""
import argparse,collections,hashlib,json,re,zipfile
from pathlib import Path


def run(epro,netlist,uuid,mcu,connectors,rails,through,out):
    if out.exists():raise ValueError('New output required')
    with zipfile.ZipFile(epro) as archive:
        files=[n for n in archive.namelist() if n.endswith('.epru')]
        if len(files)!=1:raise ValueError('Select a project with one .epru payload')
        text=archive.read(files[0]).decode('utf8')
    active=False;attrs=collections.defaultdict(dict);found=False
    for line in text.splitlines():
        if '||' not in line:continue
        h,b=line.split('||',1)
        try:h=json.loads(h);b=json.loads(b.rstrip('|'))
        except ValueError:continue
        if h['type']=='DOCHEAD':
            active=b.get('docType')=='SYMBOL' and b.get('uuid')==uuid;found|=active
        elif active and h['type']=='ATTR':attrs[b.get('parentId')][b.get('key')]=b.get('value')
    if not found:raise ValueError('Selected MCU symbol UUID not found')
    names={v['Pin Number']:v['Pin Name'] for v in attrs.values() if 'Pin Number' in v}
    nets={};current=None
    for line in netlist.read_text(encoding='utf8').split('$NETS',1)[1].splitlines():
        if line.startswith('$'):break
        if ';' in line:current,line=line.split(';',1);current=current.strip().strip("'");nets[current]=[]
        if current:nets[current]+=re.findall(r'\b[A-Za-z]+\d+\.[A-Za-z0-9]+\b',line)
    through=dict(x.split(':',1) for x in through);rows=[]
    for mapping in connectors:
        connector,offset=mapping.rsplit(':',1);offset=int(offset)
        for net,endpoints in nets.items():
            for endpoint in endpoints:
                if not endpoint.startswith(connector+'.'):continue
                pin=endpoint.split('.')[1]
                if not pin.isdecimal():raise ValueError('Only numeric connector pads are supported')
                balls=[x.split('.')[1] for x in nets.get(through.get(net,net),[]) if x.startswith(mcu+'.')]
                if net in rails:ball=None;name=net;source='module supply'
                elif len(balls)==1:ball=balls[0];name=names[ball];source='MCU via explicit channel' if net in through else 'MCU direct net'
                else:raise ValueError(f'Unresolved or ambiguous MCU endpoint: {endpoint} {net} {balls}')
                rows.append({'pin':str(int(pin)+offset),'connector':connector,'connector_pin':pin,'net':net,
                             'mcu_ball':ball,'name':name,'name_source':source,'is_supply':net in rails})
    if not rows or len({r['pin'] for r in rows})!=len(rows):raise ValueError('Empty map or duplicate module pad numbering')
    rows.sort(key=lambda r:int(r['pin']))
    report={'source_epro_sha256':hashlib.sha256(epro.read_bytes()).hexdigest(),'netlist_sha256':hashlib.sha256(netlist.read_bytes()).hexdigest(),
            'symbol_uuid':uuid,'mcu':mcu,'explicit_through_nets':through,'pins':rows}
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf8');print('MAPPED',len(rows))
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('epro','netlist','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--symbol-uuid',required=True);p.add_argument('--mcu',required=True)
    p.add_argument('--connector',action='append',required=True);p.add_argument('--rail',action='append',default=[]);p.add_argument('--through-net',action='append',default=[])
    a=p.parse_args();run(a.epro,a.netlist,a.symbol_uuid,a.mcu,a.connector,set(a.rail),a.through_net,a.out)
