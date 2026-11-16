"""UI integration fixtures only. These responses are NOT agent benchmark results."""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE=os.getenv('DEMO_URL','http://127.0.0.1:8503')
source={'id':'qa_fixture','source':'QA fixture (not benchmark)','page':3,
        'text':'<img src=x onerror="window.injected=true">\nNội dung thử hiển thị an toàn.', 'score':0.8}
question='<img src=x onerror="window.injected=true"> câu hỏi thử giao diện'

def stream(result=None,error=None):
    events=[{'type':'question','question':question},
            {'type':'searching','query':'query thật trong fixture QA','iteration':1},
            {'type':'retrieved','query':'query thật trong fixture QA','results':[source],'context_ids':['qa_fixture'],'context':source['text']}]
    events.append({'type':'error','error':error} if error else {'type':'complete','result':result})
    return '\n'.join(json.dumps(e,ensure_ascii=False) for e in events)+'\n'

with sync_playwright() as p:
    browser=p.chromium.launch()
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(BASE);page.wait_for_selector('#examples button')
    page.locator('#examples button').first.click()
    assert 'biểu hiện' in page.locator('#question').input_value()
    assert page.locator('#runCard').is_hidden(), 'Example fills the question; never submits without a click.'
    fixture={'status':'answered','answer':'Câu trả lời fixture [qa_fixture]', 'citations':['qa_fixture'],
             'sources':[source], 'elapsed_ms':1200,'search_count':1,'model_call_count':2,'model':'qa-fixture'}
    captured=[]
    def respond(route):
        captured.append(route.request.post_data_json)
        route.fulfill(status=200,content_type='application/x-ndjson',body=stream(fixture))
    page.route('**/api/chat',respond)
    page.locator('#question').fill(question);page.locator('#send').click()
    page.wait_for_function("document.getElementById('answerState').textContent === 'Có câu trả lời kèm nguồn'")
    assert captured[-1]['query']==question
    assert page.locator('#askedQuestion').inner_text()==question
    assert page.locator('.search-query').inner_text()=='query thật trong fixture QA'
    assert page.locator('.source-card blockquote').inner_text()==source['text']
    assert page.locator('.source-card img').count()==0
    assert page.evaluate('window.injected !== true')
    assert page.locator('.source-open').get_attribute('href')=='/data/pdf#page=3'
    page.locator('.citation').click();assert 'source-flash' in page.locator('.source-card').get_attribute('class')
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
    page.set_viewport_size({'width':390,'height':844})
    assert not page.evaluate('document.documentElement.scrollWidth > innerWidth')
    second={**source,'id':'qa_fixture_2','page':4}
    fixture.update(answer='Hai nguồn [qa_fixture, qa_fixture_2]. [qa_fixture] [qa_fixture_2]',citations=['qa_fixture','qa_fixture_2'],sources=[source,second])
    page.locator('#question').fill('Câu nhiều nguồn');page.locator('#send').click()
    page.wait_for_function("document.querySelectorAll('#answerBody .citation').length === 2")
    assert 'qa_fixture' not in page.locator('#answerBody').inner_text(),'Grouped IDs should render as readable source links.'
    fixture['sources']=[source]
    fixture['status']='abstain';fixture['answer']='Không đủ bằng chứng.';fixture['citations']=[]
    page.locator('#question').fill('Câu thiếu dữ liệu');page.locator('#send').click()
    page.wait_for_function("document.getElementById('answerState').textContent === 'Chưa đủ bằng chứng'")
    page.unroute('**/api/chat',respond)
    page.route('**/api/chat',lambda route:route.fulfill(status=200,content_type='application/x-ndjson',body=stream(error='Lỗi quota fixture')))
    page.locator('#question').fill('Câu thử lỗi');page.locator('#send').click()
    page.wait_for_function("document.getElementById('answerState').textContent === 'Lỗi xử lý'")
    assert page.locator('.source-card').count()==1,'Keep retrieved evidence after provider failure.'
    assert page.locator('#answerBody').is_hidden()
    page.locator('#reset').click();assert page.locator('.source-card').count()==0
    assert not errors,errors
    browser.close()
print('UI fixtures passed: question/query/evidence, safe text, citation link, abstention/error, reset, desktop/mobile.')
