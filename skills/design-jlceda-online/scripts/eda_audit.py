"""Compare LCEDA pin nets or native records. Read-only; this is not ERC/DRC or a BOM check."""
import argparse
import json
import pathlib
import sys


def unwrap(value):
    if isinstance(value, dict) and 'success' in value:
        if value['success'] is not True:
            raise ValueError('Refusing unsuccessful Bridge output')
        value = value.get('result')
    return value


def read_json(path):
    return unwrap(json.loads(pathlib.Path(path).read_text(encoding='utf-8-sig')))


def pin_map(value):
    value = unwrap(value)
    if isinstance(value, dict) and 'netlist' in value:
        value = value['netlist']
    if not isinstance(value, dict) or not isinstance(value.get('components'), dict):
        raise ValueError('Expected JLCEDA netlist with a components object')
    refs, pins = set(), {}
    for component in value['components'].values():
        ref = component.get('props', {}).get('Designator')
        if not isinstance(ref, str) or not ref or ref in refs:
            raise ValueError('Missing or duplicate Designator: ' + str(ref))
        refs.add(ref)
        info = component.get('pinInfoMap')
        if not isinstance(info, dict):
            raise ValueError('Missing pinInfoMap: ' + ref)
        for pin, data in info.items():
            if not isinstance(data, dict) or 'net' not in data:
                raise ValueError('Missing net field: ' + ref + '.' + str(pin))
            net = data['net']
            if net is not None and not isinstance(net, str):
                raise ValueError('Invalid net: ' + ref + '.' + str(pin))
            pins[ref, str(pin)] = net or ''
    return refs, pins


def compare_netlists(before, after):
    ar, ap = pin_map(before)
    br, bp = pin_map(after)
    differences = []
    for ref, pin in sorted(ap.keys() | bp.keys()):
        key = (ref, pin)
        if key not in ap or key not in bp or ap[key] != bp[key]:
            differences.append({'ref': ref, 'pin': pin, 'beforePresent': key in ap,
                                'afterPresent': key in bp, 'before': ap.get(key), 'after': bp.get(key)})
    return {'equal': ar == br and not differences, 'pinsBefore': len(ap), 'pinsAfter': len(bp),
            'componentsAdded': sorted(br-ar), 'componentsRemoved': sorted(ar-br),
            'pinChanges': differences}


def source_text(path):
    text = pathlib.Path(path).read_text(encoding='utf-8-sig')
    # A raw native file begins with a JSON header followed by ||, so whole-file JSON parsing fails.
    try:
        value = unwrap(json.loads(text))
    except json.JSONDecodeError:
        return text
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and isinstance(value.get('source'), str):
        return value['source']
    raise ValueError('Expected raw native source or a source field')


def native_records(text, ignored=('DOCHEAD', 'CANVAS', 'ACTIVE_LAYER')):
    result, anonymous = {}, {}
    decoder = json.JSONDecoder()
    for number, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        # Decode the header first: text properties can legitimately contain the characters ||.
        header, end = decoder.raw_decode(line)
        rest = line[end:].lstrip()
        if not rest.startswith('||'):
            raise ValueError(f'Native separator missing at line {number}')
        body, end = decoder.raw_decode(rest[2:].lstrip())
        tail = rest[2:].lstrip()[end:].strip()
        if tail not in ('', '|'):
            raise ValueError(f'Unexpected native record suffix at line {number}')
        typ = header.get('type')
        if not isinstance(typ, str):
            raise ValueError(f'Native type missing at line {number}')
        if typ in ignored:
            continue
        identity = header.get('id')
        if identity is None:
            anonymous[typ] = anonymous.get(typ, 0) + 1
            identity = '@anonymous:' + str(anonymous[typ])
        if not isinstance(identity, str):
            identity = json.dumps(identity, sort_keys=True)
        key = (typ, identity)
        if key in result:
            raise ValueError('Duplicate native record: ' + str(key))
        # Ticket is editor bookkeeping; preserve and compare other header semantics.
        result[key] = ({k:v for k,v in header.items() if k != 'ticket'}, body)
    if not result:
        raise ValueError('No comparable native records')
    return result


def compare_sources(before, after, allowed=(), ignored=('DOCHEAD', 'CANVAS', 'ACTIVE_LAYER')):
    a, b = native_records(before, ignored), native_records(after, ignored)
    changes = [{'type': k[0], 'id': k[1], 'change': 'added' if k not in a else 'removed' if k not in b else 'modified'}
               for k in sorted(a.keys() | b.keys()) if a.get(k) != b.get(k)]
    unexpected = [c for c in changes if c['id'] not in set(allowed)]
    return {'equal': not changes, 'withinAllowedChanges': not unexpected,
            'changes': changes, 'unexpectedChanges': unexpected}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    for name in ('netlist', 'source'):
        command = sub.add_parser(name)
        command.add_argument('before', type=pathlib.Path)
        command.add_argument('after', type=pathlib.Path)
        if name == 'source':
            command.add_argument('--allow-id', action='append', default=[])
            command.add_argument('--ignore-type', action='append', default=[],
                                 help='Additional editor-only record type to omit')
    args = parser.parse_args(argv)
    try:
        if args.mode == 'netlist':
            report = compare_netlists(read_json(args.before), read_json(args.after))
            okay = report['equal']
        else:
            report = compare_sources(source_text(args.before), source_text(args.after), args.allow_id,
                                     ('DOCHEAD','CANVAS','ACTIVE_LAYER',*args.ignore_type))
            okay = report['withinAllowedChanges']
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if okay else 1
    except (ValueError, OSError, TypeError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
