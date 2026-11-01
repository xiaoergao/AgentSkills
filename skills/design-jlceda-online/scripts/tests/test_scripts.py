"""Synthetic fixtures only. Never contact an EDA instance or import project files."""
import copy
import json
import pathlib
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from bridge_client import Bridge, BridgeError, INSPECT
from eda_audit import compare_netlists, compare_sources, pin_map


def fixture():
    return {'components': {'fake-id': {'props': {'Designator':'U1'},
            'pinInfoMap': {'1':{'net':'BUS.RX'},'2':{'net':'GND'},'3':{'net':''}}}}}


def native(value, ticket=1):
    return json.dumps({'type':'DOCHEAD'})+'||'+json.dumps({'updateTime':ticket})+'|\n'+json.dumps(
        {'type':'ATTR','id':'label-id','ticket':ticket})+'||'+json.dumps({'value':value})+'|\n'


class AuditTests(unittest.TestCase):
    def test_wrapped_and_unwrapped(self):
        self.assertTrue(compare_netlists(fixture(), {'success':True,'result':{'netlist':fixture()}})['equal'])

    def test_pin_swap_is_not_equal(self):
        after=fixture();pins=after['components']['fake-id']['pinInfoMap']
        pins['1']['net'],pins['2']['net']=pins['2']['net'],pins['1']['net']
        self.assertEqual(len(compare_netlists(fixture(),after)['pinChanges']),2)

    def test_deleted_empty_pin_is_detected(self):
        after=fixture();del after['components']['fake-id']['pinInfoMap']['3']
        self.assertFalse(compare_netlists(fixture(),after)['equal'])

    def test_pinless_component_is_detected(self):
        after=fixture();after['components']['mechanical']={'props':{'Designator':'MP1'},'pinInfoMap':{}}
        self.assertEqual(compare_netlists(fixture(),after)['componentsAdded'],['MP1'])

    def test_duplicate_designator_is_rejected(self):
        after=fixture();after['components']['second']=copy.deepcopy(after['components']['fake-id'])
        with self.assertRaises(ValueError):pin_map(after)

    def test_failed_output_is_rejected(self):
        with self.assertRaises(ValueError):pin_map({'success':False,'result':fixture()})

    def test_source_ignores_timestamp_not_content(self):
        self.assertTrue(compare_sources(native('a',1),native('a',2))['equal'])
        self.assertFalse(compare_sources(native('a'),native('b'))['withinAllowedChanges'])
        self.assertTrue(compare_sources(native('a'),native('b'),['label-id'])['withinAllowedChanges'])

    def test_delimiter_inside_text_is_valid(self):
        self.assertTrue(compare_sources(native('a||b|'),native('a||b|'))['equal'])


class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.docs={'one':{'parentProjectUuid':'original','uuid':'same-doc'},
                   'two':{'parentProjectUuid':'copy','uuid':'same-doc'}}
        self.executions=[]
        self.fail_mutation=False
        self.switch_before_mutation=False
        outer=self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def respond(self,value):
                raw=json.dumps(value).encode();self.send_response(200)
                self.send_header('Content-Type','application/json');self.end_headers();self.wfile.write(raw)
            def do_GET(self):
                self.respond({'windows':[{'windowId':w,'active':w=='one','connected':True} for w in outer.docs]})
            def do_POST(self):
                body=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                if body['code']==INSPECT:
                    self.respond({'success':True,'result':outer.docs[body['windowId']]});return
                outer.executions.append(body)
                # Simulates rejection by the injected guard; not a JavaScript interpreter.
                if outer.switch_before_mutation or outer.fail_mutation:
                    self.respond({'success':False,'error':'EDA_TARGET_CHANGED' if outer.switch_before_mutation else 'operation failed'})
                else:self.respond({'success':True,'result':{'ok':True}})
        self.server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
        self.bridge=Bridge('http://127.0.0.1:'+str(self.server.server_port),timeout=2)

    def tearDown(self):
        self.server.shutdown();self.server.server_close();self.thread.join()

    def test_duplicate_doc_ids_select_by_project(self):
        self.bridge.run('copy','same-doc','return {ok:true};')
        self.assertEqual(self.executions[0]['windowId'],'two')
        code=self.executions[0]['code']
        self.assertLess(code.index('await assertTarget();'),code.index('return {ok:true};'))
        self.assertGreater(code.rindex('await assertTarget();'),code.index('return {ok:true};'))

    def test_unknown_target_never_runs_payload(self):
        with self.assertRaises(BridgeError):self.bridge.run('absent','same-doc','return true;')
        self.assertEqual(self.executions,[])

    def test_ambiguous_target_requires_window(self):
        self.docs['three']=dict(self.docs['two'])
        with self.assertRaises(BridgeError):self.bridge.run('copy','same-doc','return true;')
        self.assertEqual(self.executions,[])
        self.bridge.run('copy','same-doc','return true;',window='three')
        self.assertEqual(self.executions[0]['windowId'],'three')

    def test_failed_write_is_not_retried(self):
        self.fail_mutation=True
        with self.assertRaises(BridgeError):self.bridge.run('copy','same-doc','return true;')
        self.assertEqual(len(self.executions),1)

    def test_switch_rejection_is_not_retried(self):
        self.switch_before_mutation=True
        with self.assertRaises(BridgeError):self.bridge.run('copy','same-doc','return true;')
        self.assertEqual(len(self.executions),1)


if __name__=='__main__':unittest.main()
