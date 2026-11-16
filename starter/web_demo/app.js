'use strict';
const $ = id => document.getElementById(id);
let meta, busy = false, sourceMap = new Map(), contextIds = new Set(), citedIds = new Set();
let steps = [], currentStep = null, sourceNodes = new Map();
const el = (tag, className, text) => {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
};
function badge(id, text, tone) { $(id).textContent = text; $(id).className = `pill ${tone}`; }
function focusSource(id) {
  const node = sourceNodes.get(id);
  if (!node) return;
  node.scrollIntoView({behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block:'center'});
  node.tabIndex = -1; node.focus({preventScroll:true});
  node.classList.add('source-flash'); setTimeout(() => node.classList.remove('source-flash'), 1500);
}
function renderSources() {
  $('sources').replaceChildren(); sourceNodes.clear();
  $('sourceCount').textContent = sourceMap.size;
  $('evidenceEmpty').hidden = sourceMap.size > 0;
  const rows = [...sourceMap.values()].sort((a,b) => Number(citedIds.has(b.id)) - Number(citedIds.has(a.id)));
  rows.forEach((source) => {
    const cited = citedIds.has(source.id), inContext = contextIds.has(source.id);
    const card = el('article', `source-card${cited?' cited':''}`);
    const top = el('div','source-top');
    top.append(el('strong','',`Trang ${source.page}`), el('span','source-tag',cited?'ĐƯỢC TRÍCH DẪN':inContext?'ĐÃ GỬI MODEL':'CHỈ TÌM ĐƯỢC'));
    card.append(top,el('p','source-location',source.source?.split(/[\\/]/).pop() || meta?.title || 'Tài liệu gốc'));
    const quote = el('blockquote','',source.text); quote.tabIndex = 0;
    quote.setAttribute('aria-label',`Đoạn trích trang ${source.page}`);card.append(quote);
    const details=el('details');details.append(el('summary','','Thông tin đoạn trích'));
    details.append(el('div','source-id',source.id),el('div','',`Điểm xếp hạng: ${typeof source.score==='number'?source.score.toPrecision(4):'không có'}`));
    card.append(details);
    const open=el('a','source-open',`Mở PDF tại trang ${source.page} ↗`);
    open.href=`/data/pdf#page=${encodeURIComponent(source.page)}`;open.target='_blank';open.rel='noopener';card.append(open);
    $('sources').append(card);sourceNodes.set(source.id,card);
  });
}
function renderAnswer(text, citations) {
  const answer=$('answerBody');answer.replaceChildren();
  const ids=new Set(citations), displayed=new Set();
  // Only transform references that the API actually returned. All other content stays plain text.
  const regex=/\[([^\]\n]+)\]/g;let previous=0;
  for (const match of text.matchAll(regex)) {
    const group=match[1].split(',').map(id=>id.trim());
    if (!group.length || !group.every(id=>ids.has(id)&&sourceMap.has(id))) continue;
    answer.append(document.createTextNode(text.slice(previous,match.index)));
    for (const id of group) {
      if (displayed.has(id)) continue;
      displayed.add(id);
      const source=sourceMap.get(id);
      const button=el('button','citation',`Nguồn · trang ${source.page}`);button.type='button';
      button.addEventListener('click',()=>focusSource(source.id));answer.append(button);
    }
    previous=match.index+match[0].length;
  }
  answer.append(document.createTextNode(text.slice(previous)));
  answer.hidden=false;$('answerEmpty').hidden=true;
}
function begin(query) {
  sourceMap.clear();contextIds.clear();citedIds.clear();steps=[];currentStep=null;
  renderSources();$('searchSteps').replaceChildren();$('runCard').hidden=false;
  $('askedQuestion').textContent=query;$('errorBox').hidden=true;
  $('answerBody').hidden=true;$('answerMeta').hidden=true;
  $('answerEmpty').hidden=false;
  $('answerEmpty').querySelector('p').textContent='Đang tìm bằng chứng cho câu hỏi của bạn.';
  $('answerEmpty').querySelector('span').textContent='Bạn có thể theo dõi query và đoạn trích ngay phía trên và bên cạnh.';
  $('liveStatus').className='loading';$('liveStatus').textContent='Đang chờ model chọn cách tìm trong tài liệu…';
  badge('runState','Đang xử lý','neutral');badge('answerState','Đang chờ bằng chứng','neutral');
}
function handleEvent(event) {
  if (event.type==='question') return;
  if (event.type==='searching') {
    currentStep=el('article','search-step');
    currentStep.append(el('span','mini-label',`LƯỢT TÌM ${event.iteration} · QUERY AGENT ĐÃ CHỌN`),el('p','search-query',event.query));
    currentStep.append(el('p','step-result','Đang truy xuất kho tài liệu…'));
    $('searchSteps').append(currentStep);
    $('liveStatus').textContent=`Agent đang tìm: “${event.query}”`;
  }
  if (event.type==='retrieved') {
    steps.push(event);contextIds=new Set(event.context_ids);
    event.results.forEach(source=>sourceMap.set(source.id,source));renderSources();
    if (currentStep) {
      currentStep.querySelector('.step-result').textContent=`Lấy được ${event.results.length} đoạn · ${event.context_ids.length} đoạn trong ngữ cảnh hiện tại.`;
      const links=el('div','step-links');
      event.results.forEach((source,i)=>{
        const button=el('button','source-shortcut',`${i+1}. Trang ${source.page}`);button.type='button';
        button.addEventListener('click',()=>focusSource(source.id));links.append(button);
      });currentStep.append(links);
    }
    $('liveStatus').textContent='Đã lấy đoạn trích thật. Model đang đối chiếu để trả lời hoặc tìm tiếp…';
  }
}
function finish(result) {
  citedIds=new Set(result.citations);
  result.sources.forEach(source=>sourceMap.set(source.id,source));renderSources();
  renderAnswer(result.answer,result.citations);
  const answered=result.status==='answered';
  badge('runState','Đã hoàn tất','success');
  badge('answerState',answered?'Có câu trả lời kèm nguồn':'Chưa đủ bằng chứng',answered?'success':'insufficient');
  $('liveStatus').className='';
  $('liveStatus').textContent=answered?'Agent đã trả lời. Bấm vào nguồn để kiểm tra đoạn trích và trang gốc.':'Agent không tìm được đủ bằng chứng sau các lượt truy xuất. Các đoạn bên cạnh không đủ để kết luận.';
  const items=[`${(result.elapsed_ms/1000).toFixed(1)} giây`,`${result.search_count} lượt tìm`,`${result.model_call_count} lần gọi model`,result.model];
  $('answerMeta').replaceChildren(...items.map(text=>el('span','',text)));$('answerMeta').hidden=false;
}
function showError(message) {
  $('errorBox').textContent=message;$('errorBox').hidden=false;
  $('answerEmpty').hidden=true;$('answerBody').hidden=true;
  badge('answerState','Lỗi xử lý','failed');badge('runState','Chưa hoàn tất','failed');
  $('liveStatus').className='';$('liveStatus').textContent='Lượt hỏi bị lỗi. Đây không phải kết luận rằng tài liệu thiếu bằng chứng.';
}
function setBusy(value) {
  busy=value;$('send').disabled=value;$('question').disabled=value;$('config').disabled=value;$('reset').disabled=value;
  document.querySelectorAll('#examples button').forEach(button=>button.disabled=value);
  $('send').replaceChildren(document.createTextNode(value?'Đang tra cứu…':'Tìm câu trả lời '));
  if (!value) $('send').append(el('span','','↗'));
  $('questionForm').setAttribute('aria-busy',String(value));
}
async function submitQuestion(event) {
  event.preventDefault();if (busy) return;
  const query=$('question').value.trim();if (!query) { $('question').focus();return; }
  begin(query);setBusy(true);
  const abort=new AbortController(), timeout=setTimeout(()=>abort.abort(),240000);
  try {
    const response=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/x-ndjson'},body:JSON.stringify({query,config:$('config').value}),signal:abort.signal});
    if (!response.ok) { const body=await response.json();throw new Error(body.error || 'Máy chủ không phản hồi.'); }
    const reader=response.body.getReader(),decoder=new TextDecoder();let pending='',complete=false;
    while (true) {
      const {value,done}=await reader.read();pending+=decoder.decode(value,{stream:!done});
      const lines=pending.split('\n');pending=lines.pop();
      for (const line of lines) {
        if (!line.trim()) continue;
        const message=JSON.parse(line);
        if (message.type==='error') throw new Error(message.error);
        if (message.type==='complete') { finish(message.result);complete=true; }
        else handleEvent(message);
      }
      if (done) break;
    }
    if (!complete) throw new Error('Kết nối kết thúc trước khi có kết quả. Hãy thử lại.');
  } catch (error) {
    showError(error.name==='AbortError'?'Đã quá thời gian chờ. Kiểm tra kết nối hoặc quota rồi thử lại.':error.message);
  } finally { clearTimeout(timeout);setBusy(false); }
}
async function loadBenchmark() {
  const container=$('benchmarkContent');
  try {
    const response=await fetch('/api/benchmark');if (!response.ok) throw new Error('Không đọc được kết quả.');
    const data=await response.json();$('benchmarkNote').textContent=data.note;
    if (!data.records.length) { container.textContent='Chưa có kết quả test đã chấm. UI sẽ hiển thị khi có summary từ lần chạy thực tế.';return; }
    const table=el('table'),head=el('thead'),tr=el('tr');
    ['Cấu hình','Câu có đáp án: điểm TB /2','Từ chối đúng','Lỗi hệ thống'].forEach(text=>{const th=el('th','',text);th.scope='col';tr.append(th);});head.append(tr);table.append(head);
    const tbody=el('tbody');
    const ratio=value=>value?`${value.n}/${value.N}`:'Chưa chấm';
    data.records.forEach(record=>{
      const row=el('tr');
      const label=meta.configs.find(c=>c.id===record.config_name)?.label || record.config_name;
      const values=[label,record.grounded_answer?.mean?.toFixed(2) ?? 'Chưa chấm',ratio(record.abstention_all_cases || record.abstention),String(record.provider_errors ?? 0)];
      values.forEach(text=>row.append(el('td','',text)));tbody.append(row);
    });table.append(tbody);const wrap=el('div','table-wrap');wrap.append(table);container.replaceChildren(wrap);
  } catch(error) {container.textContent=error.message;}
}
function tab(evaluation) {
  $('askView').hidden=evaluation;$('evaluationView').hidden=!evaluation;
  $('askTab').classList.toggle('active',!evaluation);$('evaluationTab').classList.toggle('active',evaluation);
  $('askTab').setAttribute('aria-pressed',String(!evaluation));$('evaluationTab').setAttribute('aria-pressed',String(evaluation));
  if (evaluation) loadBenchmark();
}
$('questionForm').addEventListener('submit',submitQuestion);
$('question').addEventListener('keydown',event=>{if (event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();$('questionForm').requestSubmit();}});
$('askTab').addEventListener('click',()=>tab(false));$('evaluationTab').addEventListener('click',()=>tab(true));
$('reset').addEventListener('click',()=>{
  if (busy) return;
  sourceMap.clear();contextIds.clear();citedIds.clear();renderSources();$('question').value='';
  $('runCard').hidden=true;$('answerBody').hidden=true;$('answerMeta').hidden=true;$('errorBox').hidden=true;$('answerEmpty').hidden=false;
  $('answerEmpty').querySelector('p').textContent='Bắt đầu bằng một câu hỏi ở phía trên.';
  $('answerEmpty').querySelector('span').textContent='Câu trả lời và nguồn sẽ xuất hiện tại đây.';
  badge('answerState','Chưa có câu hỏi','neutral');$('question').focus();
});
(async()=>{
  try {
    const response=await fetch('/api/config');if(!response.ok) throw new Error('Không đọc được cấu hình.');
    meta=await response.json();
    $('pageCount').textContent=`${meta.pages} trang PDF`;$('chunkCount').textContent=`${meta.chunks} đoạn được lập chỉ mục`;
    $('connection').textContent=meta.api_configured?'Đã cấu hình API':'Chưa có API key';
    $('connection').classList.toggle('warning',!meta.api_configured);
    meta.configs.forEach(config=>{
      const option=el('option','',config.label+(config.id===meta.selected?(meta.selection_frozen?' · đã chọn trên dev':' · mặc định demo, chưa chốt'):''));option.value=config.id;
      $('config').append(option);
    });$('config').value=meta.selected;
    $('modelNotice').textContent=`Model demo: ${meta.model}. Model của benchmark đã lưu: ${meta.benchmark_model}.`;
    meta.examples.forEach(example=>{
      const button=el('button','',example.label);button.type='button';button.title=example.question;
      button.addEventListener('click',()=>{$('question').value=example.question;$('question').focus();});$('examples').append(button);
    });
  } catch(error) { $('connection').textContent='Chưa đọc được cấu hình';$('connection').classList.add('warning');$('send').disabled=true;$('errorBox').hidden=false;$('errorBox').textContent=error.message; }
})();
