"""HTTP checks: private files, invalid input, and provider failure remain distinct."""
import importlib.util
import json
from pathlib import Path
import threading
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"starter"))
import unittest
import urllib.request
import urllib.error
from unittest.mock import patch


class DemoTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=Path(__file__).resolve().parents[1]/'starter/web_demo/app.py'
        spec=importlib.util.spec_from_file_location('demo_app',path)
        cls.app=importlib.util.module_from_spec(spec)
        # No live model/vector calls in HTTP contract tests.
        with patch('controller.GeminiController'), patch('retrievers.QdrantDenseRetriever'):
            spec.loader.exec_module(cls.app)

    def start_server(self, engine):
        server=self.app.make_server('127.0.0.1',0,engine=engine)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        return 'http://127.0.0.1:'+str(server.server_port)

    def test_only_whitelisted_files_are_served(self):
        base=self.start_server(None)
        for path in ('/.env','/data/questions.json','/../../.env'):
            with self.assertRaises(urllib.error.HTTPError) as cm: urllib.request.urlopen(base+path)
            self.assertEqual(cm.exception.code,404);cm.exception.close()
        with urllib.request.urlopen(base+'/') as r:self.assertEqual(r.status,200)

    def test_provider_error_is_not_abstention(self):
        class Broken:
            def ask(self,*args,**kwargs):raise ConnectionError('private provider details')
        base=self.start_server(Broken())
        request=urllib.request.Request(base+'/api/chat',data=json.dumps({'query':'question','config':'baseline'}).encode(),headers={'Content-Type':'application/json'})
        with self.assertRaises(urllib.error.HTTPError) as cm:urllib.request.urlopen(request)
        self.assertEqual(cm.exception.code,503)
        data=json.load(cm.exception)
        self.assertEqual(data['status'],'error')
        self.assertNotIn('private',data['error']);cm.exception.close()

    def test_invalid_request_has_useful_json_error(self):
        base=self.start_server(None)
        for body in ({'query':[]},{'query':'x','config':'unknown'},{'query':' '}):
            request=urllib.request.Request(base+'/api/chat',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
            with self.assertRaises(urllib.error.HTTPError) as cm:urllib.request.urlopen(request)
            self.assertEqual(cm.exception.code,400)
            self.assertEqual(json.load(cm.exception)['status'],'error');cm.exception.close()

    def test_stream_contains_real_retrieval_before_final_result(self):
        class Streaming:
            def ask(self, question, config, on_event=None):
                on_event({'type':'searching','query':'specific query','iteration':1})
                on_event({'type':'retrieved','query':'specific query','results':[{'id':'actual','text':'actual text','page':2}], 'context_ids':['actual']})
                return {'status':'abstain','answer':'Không đủ bằng chứng.','citations':[],'sources':[]}
        base=self.start_server(Streaming())
        request=urllib.request.Request(base+'/api/chat',data=json.dumps({'query':'question','config':'baseline'}).encode(),headers={'Content-Type':'application/json','Accept':'application/x-ndjson'})
        with urllib.request.urlopen(request) as response:
            self.assertEqual(response.headers['Content-Type'],'application/x-ndjson; charset=utf-8')
            rows=[json.loads(line) for line in response]
        self.assertEqual([r['type'] for r in rows],['question','searching','retrieved','complete'])
        self.assertEqual(rows[2]['results'][0]['text'],'actual text')
        self.assertEqual(rows[3]['result']['status'],'abstain')

if __name__=='__main__':unittest.main()
