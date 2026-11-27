'use strict';
const chatState={id:null,scope:'PERSONAL',busy:false,rows:[],pending:null,loading:false,generation:0,conversationScope:null};
const chatErrors={CHAT_IN_PROGRESS:'上一筆訊息仍在處理，稍後可查詢同一筆結果。',CHAT_CONTEXT_TOO_LARGE:'本輪訊息或必要限制超過情境容量，請增加容量或縮短訊息。',CHAT_MEMORY_CHANGED:'處理途中記憶已變更，這筆結果未套用。請重新送出。',CHAT_RESPONSE_INCOMPLETE:'模型回覆被截斷，沒有保存助理回答。',CHAT_RESPONSE_EMPTY:'模型回覆空白，沒有保存助理回答。',CHAT_RESPONSE_JSON_INVALID:'模型回覆格式無效，沒有保存助理回答。',LIVE_API_DISABLED:'本機未啟用 MixRoute。請確認本機 .env 設定。',BUDGET_LIMIT_REACHED:'已達原有預算上限，未新增呼叫。',CHAT_INTERRUPTED_USE_NEW_REQUEST:'上次請求已中斷。請開始新一輪訊息。'};
function chatError(code){return chatErrors[code] || `處理未完成：${text(code)}`;}
function chatStatus(message){$('#chat-status').textContent=message;}
function pendingStorage(id=chatState.id){return `rememory-chat-pending:${id}`;}
function chatControls(){
  ['#chat-project','#chat-new','#chat-model','#chat-budget'].forEach(id=>$(id).disabled=chatState.busy);
  $$('#chat-conversations button').forEach(node=>node.disabled=chatState.busy);
  $('#chat-content').disabled=!chatState.id || chatState.busy || chatState.loading || Boolean(chatState.pending);
  $('#chat-send').disabled=!chatState.id || chatState.busy || chatState.loading;
  $('#chat-send').textContent=chatState.busy?'等待 MixRoute…':chatState.pending?'查詢上次送出結果':'傳送訊息';
}
function readPending(){
  try {chatState.pending=JSON.parse(sessionStorage.getItem(pendingStorage()) || 'null');}
  catch {chatState.pending=null;}
  if(chatState.pending){$('#chat-content').value=chatState.pending.content;chatStatus('上一筆送出尚未取得結果。查詢會使用同一個 key，不另建付費請求。');}
  chatControls();
}
async function chatRequest(path,body){
  const response=await fetch(path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},credentials:'same-origin',...(body===undefined?{}:{body:JSON.stringify(body)})});
  const data=await response.json();
  if(!response.ok){const error=new Error(chatError(data.detail || data.error));error.code=data.detail || data.error;throw error;}
  return data;
}
async function initChat(){
  list(state.workspace?.projects).forEach(p=>$('#chat-project').append(option(p.id,p.name)));
  list(state.models?.fixed).forEach(m=>$('#chat-model').append(option(`FIXED:${m.id}`,`指定模型：${m.id}`)));
  if(!state.models?.enabled)chatStatus('MixRoute 尚未啟用；可以建立聊天，送出時會由後端阻擋。');
  try {await loadChats();} catch(error){chatStatus(error.message);}
}
async function loadChats(preferred=null){
  const generation=++chatState.generation;const scope=$('#chat-project').value;
  chatState.scope=scope;chatState.loading=true;chatControls();
  try{
    const data=await chatRequest(`/api/chat?project_id=${encodeURIComponent(scope)}`);
    if(generation!==chatState.generation || scope!==$('#chat-project').value)return;
    chatState.rows=data.conversations;
    const nodes=data.conversations.map(c=>button(c.title,'chat-conversation'+(c.id===chatState.id?' active':''),()=>selectChat(c.id).catch(e=>chatStatus(e.message))));
    replace('#chat-conversations',...nodes);renderChatMemories(data.memories);
    let saved;try{saved=localStorage.getItem(`rememory-chat-selected:${scope}`);}catch{}
    const id=preferred || (data.conversations.some(c=>c.id===chatState.id)?chatState.id:null) || (data.conversations.some(c=>c.id===saved)?saved:null) || data.conversations[0]?.id;
    if(id)await selectChat(id,generation);
    else {chatState.id=null;chatState.pending=null;chatState.conversationScope=null;replace('#chat-messages',empty('新增聊天後，直接輸入你的需求。'));$('#chat-conversation-title').textContent='先新增聊天';$('#chat-context').textContent='等待對話';$('#chat-usage').textContent='';}
  }finally{if(generation===chatState.generation){chatState.loading=false;chatControls();}}
}
async function selectChat(id,generation=null){
  if(chatState.busy)return;
  generation=generation ?? ++chatState.generation;
  const scope=chatState.scope;chatState.loading=true;chatControls();
  try{
    const data=await chatRequest(`/api/chat/conversations/${encodeURIComponent(id)}`);
    if(generation!==chatState.generation || scope!==chatState.scope || scope!==$('#chat-project').value || data.conversation.project_id!==scope)return;
    if(chatState.id!==id){$('#chat-context').textContent='已保存對話';$('#chat-usage').textContent='';$('#chat-content').value='';}
    chatState.id=id;chatState.conversationScope=scope;try{localStorage.setItem(`rememory-chat-selected:${scope}`,id);}catch{}
    $('#chat-conversation-title').textContent=data.conversation.title;
    $$('#chat-conversations button').forEach((node,i)=>node.classList.toggle('active',chatState.rows[i]?.id===id));
    const messages=data.messages.map(m=>{
      const row=el('article',`chat-message chat-${m.role}`);
      append(row,el('strong','',m.role==='user'?'你':'MixRoute'),el('p','',m.content));
      if(m.status!=='COMPLETED')row.append(el('small','muted',m.status==='FAILED'?chatError(m.error || 'CHAT_INTERRUPTED'):'處理中…'));
      return row;
    });
    replace('#chat-messages',...messages.length?messages:[empty('從現在的需求開始聊，值得保留的記憶會出現在右側。')]);
    renderChatMemories(data.memories);readPending();
    $('#chat-messages').scrollTop=$('#chat-messages').scrollHeight;
  }finally{if(generation===chatState.generation){chatState.loading=false;chatControls();}}
}
const chatKind={GOAL:'目標',CONSTRAINT:'限制',DECISION:'決定',PREFERENCE:'偏好',NOTE:'筆記'};
function renderChatMemories(rows){
  const cards=rows.map(m=>{
    const card=el('article','chat-memory');
    append(card,badge(m.status==='CONFIRMED'?'已確認':'候選記憶',m.status==='CONFIRMED'?'teal':'amber'),el('small','muted',chatKind[m.kind] || m.kind),el('p','',m.content),el('small','muted',`來源訊息：${m.source_message_id}`),el('blockquote','',m.source_quote));
    if(m.edited_by_user)card.append(el('small','muted','已由你修正；下方引用保留原始來源。'));
    const actions=el('div','inline-controls');
    if(m.status!=='CONFIRMED')actions.append(button('確認','button secondary small',()=>changeChatMemory(m,'CONFIRM')));
    actions.append(button('修正','button secondary small',()=>{
      actions.hidden=true;const edit=el('textarea');edit.value=m.content;edit.maxLength=4000;edit.setAttribute('aria-label','修正記憶文字');
      append(card,edit,button('儲存修正','button primary small',()=>changeChatMemory(m,'EDIT',edit.value)),button('取消','button secondary small',()=>renderChatMemories(rows)));
    }),button('忘記','button secondary small',()=>changeChatMemory(m,'FORGET')));
    card.append(actions);return card;
  });
  replace('#chat-memories',...cards.length?cards:[empty('尚無記憶。對話後會自動整理候選項目。')]);
}
async function changeChatMemory(m,action,content){
  try{await chatRequest(`/api/chat/memories/${encodeURIComponent(m.id)}`,{action,...(content===undefined?{}:{content})});await loadChats(chatState.id);chatStatus(action==='FORGET'?'已停止載入這項記憶；原始聊天與版本仍保留。':'記憶已保存。');}
  catch(error){chatStatus(error.message);}
}
$('#chat-project').addEventListener('change',()=>{chatState.id=null;$('#chat-content').value='';loadChats().catch(e=>chatStatus(e.message));});
$('#chat-new').addEventListener('click',async()=>{
  if(chatState.busy)return;chatState.busy=true;chatControls();
  try{const c=await chatRequest('/api/chat/conversations',{project_id:$('#chat-project').value});chatState.busy=false;$('#chat-content').value='';await loadChats(c.id);$('#chat-content').focus();chatStatus('聊天已建立，沒有新增 API 呼叫。');}
  catch(error){chatStatus(error.message);}finally{chatState.busy=false;chatControls();}
});
$('#chat-form').addEventListener('submit',async event=>{
  event.preventDefault();if(chatState.busy || chatState.loading || !chatState.id || chatState.conversationScope!==$('#chat-project').value)return;
  const conversationId=chatState.id;const storageKey=pendingStorage(conversationId);
  const choice=$('#chat-model').value;
  const body=chatState.pending || {content:$('#chat-content').value,idempotency_key:crypto.randomUUID(),mode:choice==='SMART'?'SMART':'FIXED',model:choice==='SMART'?null:choice.slice(6),budget:Number($('#chat-budget').value)};
  if(!body.content.trim())return;
  chatState.pending=body;try{sessionStorage.setItem(storageKey,JSON.stringify(body));}catch{}
  chatState.busy=true;chatControls();$('#chat-usage').textContent='本輪用量等待回傳。';chatStatus('正在呼叫 MixRoute；訊息與費用由後端保存。');
  try{
    const result=await chatRequest(`/api/chat/conversations/${encodeURIComponent(conversationId)}/messages`,body);
    chatState.pending=null;try{sessionStorage.removeItem(storageKey);}catch{}
    if(result.status==='COMPLETED'){
      $('#chat-content').value='';chatStatus(result.stored_replay?'已讀回上次結果，沒有新增呼叫。':`回答已保存，新增 ${result.new_memories.length} 項候選記憶。${result.warnings.join(' ')}`);
      $('#chat-context').textContent=`載入 ${result.context.memory_count} 項記憶 · ${result.context.history_messages} 則歷史`;
    } else chatStatus(chatError(result.error));
    if(result.usage)$('#chat-usage').textContent=`實際模型：${result.usage.model || '未知'} · ${fmt(result.usage.total_tokens)} Token · 保守費用上限 ${money(result.usage.cost_upper_bound_usd)} · 實際帳單未知`;
    if(!result.usage)$('#chat-usage').textContent='本輪沒有可用的模型用量收據。';
    chatState.busy=false;await loadChats(conversationId);
  }catch(error){
    if(error.code && error.code!=='CHAT_IN_PROGRESS'){chatState.pending=null;try{sessionStorage.removeItem(storageKey);}catch{}}
    chatStatus(error.code?error.message:'連線尚未取得結果，請查詢上次送出結果。');
  }finally{chatState.busy=false;chatControls();}
});
