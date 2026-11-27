const $=s=>document.querySelector(s);
function node(tag,text){const n=document.createElement(tag);n.textContent=text;return n;}
Promise.all([fetch('assets/live-demo.json').then(r=>r.json()),fetch('assets/final-live.json').then(r=>r.json()),fetch('assets/manifest.json').then(r=>r.json())]).then(([demo,benchmark,manifest])=>{
 function stage(index){
  const s=demo.stages[index],c=s.model_call,a=s.artifact;
  $('#model-name').textContent=c.model;
  $('#stage1').setAttribute('aria-pressed',index===0);$('#stage2').setAttribute('aria-pressed',index===1);
  const stats=[['模式',s.mode],['要求模型',c.requested_model],['原始歷史',String(s.raw_history_count)],['已知 Tokens',c.total_tokens.toLocaleString()],['API 耗時',`${Math.round(c.latency_ms).toLocaleString()} ms`],['實際帳單','UNKNOWN']];
  $('#call-stats').replaceChildren(...stats.flatMap(([k,v])=>[node('dt',k),node('dd',v)]));
  $('#identifiers').replaceChildren(...[['Request',c.request_id||c.response_id],['Session',s.session_id],['SHA256',a.sha256]].map(([k,v])=>node('p',`${k} · ${v}`)));
  $('#artifact-content').textContent=a.content;$('#artifact-download').href=`assets/stage${index+1}.md`;
 }
 $('#stage1').addEventListener('click',()=>stage(0));$('#stage2').addEventListener('click',()=>stage(1));stage(0);
 const proof=demo.stages[1].handoff_proof;
 $('#proof-status').textContent=proof.prior_artifact_loaded?'已核對：前一成品的完整內容與 SHA，確實出現在第二階段模型上下文。':'尚未通過前一成品核對。';
 $('#proof-sha').textContent=proof.prior_sha256;$('#prior-content').textContent=proof.prior_content;
 $('#benchmark-rows').replaceChildren(...benchmark.results.map(r=>{
  const tr=node('tr','');const labels={E:'E · Fixed',F:'F · SMART / auto',OTHER:'Sonnet · 六案例子集'};
  [labels[r.arm],`${Math.round((r.task_success_rate||0)*r.actionable_cases)} / ${r.actionable_cases}`,r.expected_stop_cases?`${Math.round(r.stop_success_rate*r.expected_stop_cases)} / ${r.expected_stop_cases}`:'未測',Object.keys(r.actual_models).join(', '),r.known_api_tokens.toLocaleString()].forEach(v=>tr.append(node('td',v)));return tr;
 }));
 $('#source-sha').textContent=`原始碼包 SHA-256：${manifest.source_sha256}`;
}).catch(()=>{$('#model-name').textContent='紀錄暫時無法載入，請下載下方完整證據檔核對。';});
