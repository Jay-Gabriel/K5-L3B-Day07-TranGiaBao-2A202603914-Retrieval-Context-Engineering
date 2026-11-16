"""Local demo: explicit routes, lazy retrievers, evidence and provider errors."""
import argparse
import http.server
import json
import os
import sys
import threading
import time
import urllib.parse
from pathlib import Path

WEB = Path(__file__).resolve().parent
sys.path.insert(0, str(WEB.parent))
from configs import CAMPAIGN, CONFIGS, ROOT, RESULTS, build_retrievers, load_data
from agentic import run_agent
from controller import GeminiController

PDF = ROOT / 'data/cme2._suy_timgs_minh.pdf'
LABELS = {'baseline': 'Từ khóa · ngữ cảnh ngắn', 'dense': 'Ngữ nghĩa · Qdrant Day 6',
          'hybrid': 'Kết hợp · ngữ cảnh ngắn', 'hybrid_context': 'Kết hợp · ngữ cảnh mở rộng',
          'lexical_context': 'Từ khóa · ngữ cảnh mở rộng'}
EXAMPLES = [
    {'label': 'Tìm thông tin', 'question': 'Hai biểu hiện lâm sàng chính của suy tim được bài giảng nêu là gì?'},
    {'label': 'Giải thích khái niệm', 'question': 'Theo phân độ NYHA trong bài giảng, mức III được mô tả thế nào về vận động và triệu chứng khi nghỉ?'},
    {'label': 'Thử câu thiếu dữ liệu', 'question': 'Theo tài liệu, một lần tái khám suy tim ở Bệnh viện Đại học Y Dược Huế có giá bao nhiêu đồng?'},
]


def selected_config():
    path = RESULTS / 'selection.json'
    return json.loads(path.read_text())['selected'] if path.exists() else 'lexical_context'


class Engine:
    def __init__(self):
        self.chunks, _, _ = load_data()
        self.retrievers = build_retrievers(self.chunks, ['tfidf'])
        self.lock = threading.Lock()

    def ask(self, question, config_name, on_event=None):
        config = CONFIGS[config_name]
        with self.lock:
            if config['method'] not in self.retrievers:
                self.retrievers.update(build_retrievers(self.chunks, [config['method']]))
            retriever = self.retrievers[config['method']]
        controller = GeminiController(model=os.getenv('DEMO_GEMINI_MODEL'), max_searches=config['max_searches'])
        started = time.perf_counter()
        result = run_agent(question, controller, retriever, max_searches=config['max_searches'],
                           top_k=config['top_k'], budget=config['budget'], on_event=on_event)
        searches = [e for e in result['events'] if e['event'] == 'search']
        final_ids = searches[-1]['context_ids'] if searches else []
        by_id = {r['id']: r for e in searches for r in e['results']}
        sources = [{**by_id[cid], 'cited': cid in result['citations']} for cid in final_ids]
        return {'status': result['status'], 'answer': result['answer'], 'citations': result['citations'],
                'sources': sources, 'config_name': config_name, 'config': config, 'model': controller.model,
                'elapsed_ms': round((time.perf_counter()-started)*1000), 'search_count': len(searches),
                'model_call_count': len(controller.calls),
                'tokens': sum(c['usage'].get('totalTokenCount', 0) for c in controller.calls),
                'steps': [{'query': e['query'], 'result_count': len(e['results']),
                           'pages': list(dict.fromkeys(r['page'] for r in e['results'])),
                           'context_ids': e['context_ids']} for e in searches]}


def metadata():
    manifest=json.loads((ROOT/'data/corpus_manifest.json').read_text())
    return {'title': 'Chẩn đoán và Điều trị Suy tim', 'author': 'GS. TS. Huỳnh Văn Minh',
            'pages': manifest['pdf_pages'], 'chunks': manifest['chunks'], 'selected': selected_config(),
            'selection_frozen': (RESULTS / 'selection.json').exists(),
            'model': os.getenv('DEMO_GEMINI_MODEL',os.getenv('GEMINI_MODEL','gemini-2.5-flash-lite')).removeprefix('models/'),
            'benchmark_model': os.getenv('GEMINI_MODEL','gemini-2.5-flash-lite').removeprefix('models/'),
            'api_configured': bool(os.getenv('GEMINI_API_KEY')), 'examples': EXAMPLES,
            'configs': [{'id': key, 'label': value} for key,value in LABELS.items()]}


class DemoHandler(http.server.BaseHTTPRequestHandler):
    def json_response(self, data, status=200):
        body=json.dumps(data,ensure_ascii=False).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','no-store')
        self.end_headers();self.wfile.write(body)

    def do_GET(self):
        path=urllib.parse.urlparse(self.path).path
        files={'/': (WEB/'index.html','text/html; charset=utf-8'),
               '/index.html': (WEB/'index.html','text/html; charset=utf-8'),
               '/app.css': (WEB/'app.css','text/css; charset=utf-8'),
               '/app.js': (WEB/'app.js','text/javascript; charset=utf-8'),
               '/data/pdf': (PDF,'application/pdf')}
        if path in files:
            file,mime=files[path]
            if not file.exists():return self.json_response({'status':'error','error':'Không tìm thấy tài liệu.'},404)
            body=file.read_bytes()
            self.send_response(200);self.send_header('Content-Type',mime)
            self.send_header('Content-Length',str(len(body)));self.send_header('X-Content-Type-Options','nosniff')
            self.end_headers();self.wfile.write(body);return
        if path=='/api/config':return self.json_response(metadata())
        if path=='/api/benchmark':
            records=[]
            for p in sorted((RESULTS/'agent/test').glob('*/summary.json')):
                record=json.loads(p.read_text());record['config_name']=p.parent.name
                _,_,cases=load_data()
                total=sum(c['split']=='test' and not c['answerable'] for c in cases)
                record['abstention_all_cases']={'n':record['abstention']['n'],'N':total}
                records.append(record)
            return self.json_response({'records':records,'version':CAMPAIGN,
                'note':'Nhãn đã được AI hỗ trợ đọc câu trả lời/context và đối chiếu nguồn gốc; không tự động suy ra từ ID citation. Điểm số chỉ mô tả bộ câu hỏi này.'})
        self.json_response({'status':'error','error':'Không tìm thấy đường dẫn.'},404)

    def do_POST(self):
        if self.path!='/api/chat':return self.json_response({'status':'error','error':'Không tìm thấy đường dẫn.'},404)
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size<1 or size>16000:raise ValueError('Dữ liệu gửi không hợp lệ hoặc quá dài.')
            data=json.loads(self.rfile.read(size))
            if not isinstance(data,dict):raise ValueError('Dữ liệu phải là JSON object.')
            query=data.get('query')
            config=data.get('config',selected_config())
            if not isinstance(query,str) or not query.strip():raise ValueError('Hãy nhập câu hỏi trước khi gửi.')
            if len(query)>1200:raise ValueError('Câu hỏi tối đa 1.200 ký tự.')
            if not isinstance(config,str) or config not in CONFIGS:raise ValueError('Cách tìm tài liệu không hợp lệ.')
        except (ValueError,TypeError,json.JSONDecodeError) as e:
            return self.json_response({'status':'error','error':str(e)},400)
        # The UI serves locally and only accepts requests from its own origin.
        origin=self.headers.get('Origin')
        if origin and origin!=f'http://{self.headers.get("Host")}':
            return self.json_response({'status':'error','error':'Nguồn yêu cầu không hợp lệ.'},403)
        streaming = self.headers.get('Accept') == 'application/x-ndjson'
        if streaming:
            self.send_response(200)
            self.send_header('Content-Type', 'application/x-ndjson; charset=utf-8')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Connection', 'close')
            self.end_headers()
            self.close_connection = True
            def emit(event):
                self.wfile.write((json.dumps(event, ensure_ascii=False)+'\n').encode())
                self.wfile.flush()
            try:
                emit({'type': 'question', 'question': query.strip(), 'config_name': config})
                result = self.server.engine.ask(query.strip(), config, on_event=emit)
                emit({'type': 'complete', 'result': result})
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception:
                try:
                    emit({'type': 'error', 'error': 'Không hoàn tất được yêu cầu. Kiểm tra kết nối, API key hoặc quota rồi thử lại. Các đoạn đã tìm được vẫn hiển thị bên dưới.'})
                except (BrokenPipeError, ConnectionResetError):
                    pass
            return
        try:
            result=self.server.engine.ask(query.strip(),config)
            self.json_response(result)
        except (ConnectionError,TimeoutError,OSError):
            self.json_response({'status':'error','error':'Chưa kết nối được model hoặc kho tài liệu. Kiểm tra mạng, API key và quota rồi thử lại.'},503)
        except Exception:
            self.json_response({'status':'error','error':'Không xử lý được phản hồi model. Hãy thử lại hoặc xem log máy chủ.'},503)

    def log_message(self, fmt, *args):
        # Log HTTP status only; never print request bodies or credentials.
        pass


def make_server(host,port,engine=None):
    server=http.server.ThreadingHTTPServer((host,port),DemoHandler)
    server.engine=engine if engine is not None else Engine()
    return server


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--host',default='127.0.0.1');parser.add_argument('--port',type=int,default=8502)
    args=parser.parse_args()
    with make_server(args.host,args.port) as server:
        print(f'Demo: http://{args.host}:{args.port}',flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass

if __name__=='__main__':main()
