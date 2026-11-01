"""API Gateway Bridge client. Caller supplies authorized JavaScript; never retries writes."""
import argparse
import json
import pathlib
import sys
import urllib.error
import urllib.request


INSPECT = 'return await eda.dmt_SelectControl.getCurrentDocumentInfo();'


class BridgeError(RuntimeError):
    pass


class Bridge:
    def __init__(self, url='http://127.0.0.1:49620', timeout=35):
        self.url = url.rstrip('/')
        self.timeout = timeout
        # Loopback traffic must not accidentally go through a configured proxy.
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request(self, path, body=None):
        data = None if body is None else json.dumps(body, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(self.url + path, data=data,
                                     headers={'Content-Type': 'application/json; charset=utf-8'})
        try:
            with self.opener.open(req, timeout=self.timeout) as response:
                value = json.loads(response.read().decode('utf-8-sig'))
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise BridgeError('Bridge request failed; execution state may be unknown. '
                              'Read back before retrying a mutation. ' + str(exc)) from exc
        if not isinstance(value, dict):
            raise BridgeError('Unexpected Bridge response type')
        return value

    def execute(self, window, code):
        response = self.request('/execute', {'windowId': window, 'code': code})
        if response.get('success') is not True:
            raise BridgeError('Bridge execution failed: ' + str(response.get('error', 'unknown error')))
        return response

    def inventory(self):
        windows = self.request('/eda-windows').get('windows')
        if not isinstance(windows, list):
            raise BridgeError('Missing windows list')
        result = []
        for item in windows:
            entry = {'windowId': item['windowId'], 'active': item.get('active', False)}
            if item.get('connected') is False:
                entry['error'] = 'disconnected'
            else:
                try:
                    entry['doc'] = self.execute(item['windowId'], INSPECT).get('result')
                except BridgeError as exc:
                    entry['error'] = str(exc)
            result.append(entry)
        return result

    def run(self, project, document, code, window=None):
        inventory = self.inventory()
        matches = [item for item in inventory
                   if isinstance(item.get('doc'), dict)
                   and item['doc'].get('parentProjectUuid') == project
                   and item['doc'].get('uuid') == document
                   and (window is None or item['windowId'] == window)]
        if len(matches) != 1:
            raise BridgeError(f'Expected one matching project/document window; found {len(matches)}. '
                              'Use list, open the intended page, or disambiguate with --window.')
        target = json.dumps({'project': project, 'document': document})
        guarded = (
            'const expectedTarget=' + target + ';\n'
            'async function assertTarget(){\n'
            ' const d=await eda.dmt_SelectControl.getCurrentDocumentInfo();\n'
            ' if(!d||d.parentProjectUuid!==expectedTarget.project||d.uuid!==expectedTarget.document)'
            'throw Error("EDA_TARGET_CHANGED: stop and read back; do not replay");\n'
            ' return d;\n}\n'
            'await assertTarget();\n'
            'const operationResult=await (async()=>{\n' + code + '\n})();\n'
            'await assertTarget();\nreturn operationResult;'
        )
        return self.execute(matches[0]['windowId'], guarded)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:49620')
    parser.add_argument('--timeout', type=float, default=35)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('list')
    run = sub.add_parser('run')
    run.add_argument('--project', required=True)
    run.add_argument('--document', required=True)
    run.add_argument('--window')
    run.add_argument('--code-file', type=pathlib.Path, required=True)
    run.add_argument('--out', type=pathlib.Path, required=True)
    args = parser.parse_args(argv)
    try:
        bridge = Bridge(args.url, args.timeout)
        if args.command == 'list':
            print(json.dumps(bridge.inventory(), ensure_ascii=False, indent=2))
        else:
            # Refuse to overwrite a prior snapshot; failed execution also retains its evidence.
            with args.out.open('x', encoding='utf-8') as handle:
                try:
                    result = bridge.run(args.project, args.document,
                                        args.code_file.read_text(encoding='utf-8-sig'), args.window)
                except (BridgeError, OSError) as exc:
                    json.dump({'success': False, 'error': str(exc)}, handle, ensure_ascii=False, indent=2)
                    raise
                json.dump(result, handle, ensure_ascii=False, indent=2)
            print(json.dumps({'success': True, 'output': str(args.out)}, ensure_ascii=False))
    except (BridgeError, OSError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
