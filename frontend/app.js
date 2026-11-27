'use strict';

// All imported values are rendered as text. No credentials or evaluator truth
// enter this client, and all requests remain on the application's own origin.
const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const list = value => Array.isArray(value) ? value : [];
const knownNumber = value => typeof value === 'number' && Number.isFinite(value);
const fmt = (value, digits = 0) => knownNumber(value) ? value.toLocaleString('en-US', { maximumFractionDigits: digits }) : 'UNKNOWN';
const money = value => knownNumber(value) ? `US$${value.toFixed(value > 0 && value < 0.01 ? 6 : 4)}` : 'UNKNOWN';
const percentage = value => knownNumber(value) ? `${(value * 100).toFixed(1)}%` : 'UNKNOWN';
const text = value => {
  if (value === null || value === undefined) return 'UNKNOWN';
  if (typeof value === 'string') return value;
  if (typeof value === 'object') return JSON.stringify(value, null, 2);
  return String(value);
};
const compactText = value => {
  if (value && typeof value === 'object') return text(value.content ?? value.detail ?? value.reason ?? value.title ?? value.name ?? value.id ?? value);
  return text(value);
};
function el(tag, className = '', content) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (content !== undefined) node.textContent = text(content);
  return node;
}
function append(parent, ...children) { children.filter(Boolean).forEach(child => parent.append(child)); return parent; }
function replace(selector, ...children) { $(selector).replaceChildren(...children.filter(Boolean)); }
function badge(content, tone = 'neutral') { return el('span', `badge badge-${tone}`, content); }
function empty(message) { return el('div', 'empty-state', message); }
function button(content, className, callback) {
  const node = el('button', className, content);
  node.type = 'button';
  node.addEventListener('click', callback);
  return node;
}
function notify(message, type = '') {
  const node = $('#global-message');
  node.textContent = message;
  node.className = `notice ${type}`;
  node.hidden = !message;
}
function setBusy(node, busy, message) {
  if (busy) { node.dataset.idleLabel = node.textContent; node.textContent = message; }
  else { node.textContent = node.dataset.idleLabel || node.textContent; }
  node.disabled = busy;
  node.classList.toggle('loading', busy);
}
const state = {
  workspace: null, models: null, memory: null, kind: 'ALL',
  rounds: [], retrieval: null, retrieving: false, memoryRequest: 0,
  session: null, execution: null, executing: false, creatingSession: false,
  repairing: false, quickBusy: false, quickBudget: null,
  liveDemo: null, demoBusy: false,
  benchmark: null,
};
const viewNames = { workspace: 'Workspace', memory: 'Memory Explorer', observatory: 'Retrieval Observatory', context: 'Context Inspector', recovery: 'Recovery Lab', benchmark: 'Benchmark Lab' };
function navigate(view, updateHash = true) {
  if (!viewNames[view]) view = 'workspace';
  $$('.view').forEach(node => { node.hidden = node.id !== `view-${view}`; });
  $$('[data-view]').forEach(node => {
    if (node.dataset.view === view) node.setAttribute('aria-current', 'page');
    else node.removeAttribute('aria-current');
  });
  $('#current-view-name').textContent = viewNames[view];
  if (updateHash && location.hash !== `#${view}`) history.replaceState(null, '', `#${view}`);
  if (view === 'recovery') $('#recovery-budget').textContent = `${fmt(Number($('#budget').value) / 1024)}K tokens`;
}
async function api(path, body) {
  const response = await fetch(path, {
    method: body === undefined ? 'GET' : 'POST',
    headers: body === undefined ? { Accept: 'application/json' } : { Accept: 'application/json', 'Content-Type': 'application/json' },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    credentials: 'same-origin',
  });
  let data;
  try { data = await response.json(); }
  catch { throw new Error(`後端未回傳 JSON（HTTP ${response.status}）。請確認 RE:MEMORY 的啟動位址。`); }
  if (!response.ok || data?.error) throw new Error(text(data?.error ?? data?.detail ?? `HTTP ${response.status}`));
  return data;
}
function projectName(id) { return list(state.workspace?.projects).find(project => project.id === id)?.name || id || '未辨識專案'; }
function option(value, content) { const node = el('option', '', content); node.value = value; return node; }
function metric(label, value, footnote = '', small = false) {
  const node = el('div', 'context-stat');
  const number = el('strong', small ? 'small-value' : '', value);
  if (value === 'UNKNOWN') number.classList.add('metric-unknown');
  return append(node, el('span', '', label), number, el('p', '', footnote));
}

function renderWorkspace(data) {
  const projects = list(data.projects), tasks = list(data.tasks), events = list(data.events);
  $('#project-count').textContent = `${fmt(projects.length)} projects`;
  $('#reference-date').textContent = data.reference_date ? `Reference · ${data.reference_date}` : 'Reference · UNKNOWN';
  const cards = projects.map(project => {
    const card = button('', 'project-card', () => {
      $('#memory-project').value = project.id;
      $('#memory-search').value = '';
      navigate('memory');
      loadMemory();
    });
    card.dataset.testid = 'project-card';
    const open = tasks.filter(task => task.project_id === project.id && !['COMPLETED', 'DONE', 'CANCELLED'].includes(task.status)).length;
    return append(card,
      append(el('div', 'project-type'), el('span', '', project.topic || 'PROJECT'), el('span', '', project.id)),
      el('h3', '', project.name), el('p', '', project.description || '探索這個專案的已保存記憶。'),
      append(el('div', 'project-foot'), el('span', '', `${open} open tasks`), el('span', '', project.last_active || 'Date UNKNOWN')),
    );
  });
  replace('#project-list', ...(cards.length ? cards : [empty('尚無保存的專案。')]));
  const activities = [...events].sort((a, b) => String(b.date || '').localeCompare(String(a.date || ''))).slice(0, 7).map(event => {
    const node = el('div', 'activity-item');
    const info = append(el('div'), el('p', '', event.detail), el('small', '', `${projectName(event.project_id)} · ${event.type}`));
    const date = el('time', '', event.date || 'UNKNOWN');
    if (event.date) date.dateTime = event.date;
    return append(node, el('div', 'activity-icon', event.type?.includes('COMPLETE') ? '✓' : '◇'), info, date);
  });
  replace('#activity-list', ...(activities.length ? activities : [empty('尚無活動紀錄。')]));
  const labels = { projects: 'Projects', facts: 'Fact cells', aliases: 'Aliases', artifacts: 'Artifacts' };
  replace('#workspace-stats', ...Object.entries(labels).map(([key, label]) => append(el('div', 'stat-cell'), el('strong', '', fmt(data.stats?.[key])), el('span', '', label))));
  const openTasks = tasks.filter(task => !['COMPLETED', 'DONE', 'CANCELLED'].includes(task.status)).slice(0, 5);
  replace('#open-tasks', ...(openTasks.length ? openTasks.map(task => append(el('div', 'task-item'), el('span', 'task-box'), append(el('div'), el('p', '', task.title), el('small', '', `${projectName(task.project_id)} · ${task.status}`)))) : [empty('目前沒有未完成工作。')]));
  const resources = data.resources || {};
  const usage = [
    ['Actual API calls', fmt(resources.api_calls)], ['Total API tokens', fmt(resources.api_tokens)],
    ['Known token subtotal', fmt(resources.known_api_tokens)], ['Usage-unknown calls', fmt(resources.usage_unknown_calls)],
    ['Actual API cost', money(resources.api_cost_usd)], ['Outstanding reservation', money(resources.api_reserved_usd)],
  ];
  replace('#resource-usage', ...usage.map(([label, value]) => append(el('div', 'resource-line'), el('span', '', label), el('strong', '', value))));
  const spend = resources.api_cost_usd, reservation = resources.api_reserved_usd;
  $('#resource-bar').style.width = knownNumber(spend) && knownNumber(reservation) ? `${Math.min(100, Math.max(0, (spend + reservation) / 35 * 100))}%` : '0%';
  $('#resource-bar').title = knownNumber(spend) && knownNumber(reservation) ? `${money(spend + reservation)} committed or reserved` : 'UNKNOWN';
  const previousProject = $('#memory-project').value;
  $('#memory-project').replaceChildren(...projects.map(project => option(project.id, `${project.name} · ${project.id}`)));
  if (projects.some(project => project.id === previousProject)) $('#memory-project').value = previousProject;
  $$('[data-testid="dataset-label"]').forEach(node => { node.textContent = `${text(data.dataset)} DATASET`; });
  renderModelSelection();
}

async function loadMemory() {
  const projectId = $('#memory-project').value;
  if (!projectId) return;
  const request = ++state.memoryRequest;
  $('#memory-load-state').textContent = 'Loading…';
  try {
    const params = new URLSearchParams({ project_id: projectId, q: $('#memory-search').value.trim() });
    const data = await api(`/api/memory?${params}`);
    if (request !== state.memoryRequest) return;
    state.memory = data;
    renderMemory();
    $('#memory-load-state').textContent = `Loaded · ${list(data.facts).length} fact cells`;
  } catch (error) {
    if (request !== state.memoryRequest) return;
    $('#memory-load-state').textContent = 'Load failed';
    replace('#fact-list', empty(error.message));
    notify(`記憶載入失敗：${error.message}`, 'error');
  }
}
function renderMemory() {
  const data = state.memory;
  if (!data) return;
  $('#memory-project-title').textContent = data.project?.name || projectName($('#memory-project').value);
  const facts = list(data.facts).filter(fact => state.kind === 'ALL' || fact.kind === state.kind);
  const factCards = facts.map(fact => {
    const node = el('article', `fact-card${fact.conflict ? ' fact-conflict' : ''}`);
    node.dataset.testid = 'memory-fact';
    const tone = fact.kind === 'CONSTRAINT' ? 'amber' : fact.kind === 'GOAL' ? 'teal' : 'neutral';
    const header = append(el('div', 'fact-top'), badge(fact.kind || 'UNKNOWN', tone), el('code', '', fact.id));
    const metadata = append(el('div', 'metadata-row'),
      el('span', '', `Version ${text(fact.version)}`), el('span', '', `Trust ${text(fact.trust)}`),
      el('span', '', text(fact.verification)),
      fact.superseded ? badge('SUPERSEDED', 'amber') : null, fact.conflict ? badge('CONFLICT', 'red') : null,
    );
    append(node, header, el('p', '', fact.content), metadata, el('div', 'evidence-ref', `Evidence · ${list(fact.evidence_ids).join(', ') || 'NONE RECORDED'}`));
    if (!fact.superseded && fact.verification === 'VERIFIED' && ['SOURCE', 'USER'].includes(fact.trust) && !['CLAIM', 'INFERENCE', 'UNKNOWN'].includes(fact.kind)) {
      const edit = button('依來源修正', 'button secondary small', () => {
        if (node.querySelector('form')) return;
        node.append(factRevisionForm(fact));
      });
      edit.dataset.testid = 'revise-fact'; node.append(edit);
    }
    return node;
  });
  replace('#fact-list', ...(factCards.length ? factCards : [empty('目前的搜尋與類型沒有符合記憶。')]));
  const aliases = list(data.aliases).map(alias => {
    const tone = alias.status === 'CONFIRMED' ? 'teal' : alias.ambiguous ? 'amber' : 'neutral';
    const node = append(el('div', 'alias-item'), append(el('div', 'alias-top'), el('strong', '', alias.alias), badge(alias.status, tone)), el('small', '', `${fmt(alias.uses)} uses · strength ${fmt(alias.strength, 3)}${alias.ambiguous ? ' · AMBIGUOUS' : ''}`));
    if (alias.status === 'CANDIDATE') {
      const confirm = button('確認此專案稱呼', 'button secondary small', async () => {
        try { await memoryMutation(`/api/memory/aliases/${encodeURIComponent(alias.id)}/confirm`, {}, confirm, '稱呼已確認；其他同名稱呼仍保留。'); }
        catch (error) { notify(`稱呼確認失敗：${error.message}`, 'error'); }
      });
      confirm.dataset.testid = 'confirm-alias'; node.append(confirm);
    }
    return node;
  });
  replace('#alias-list', ...(aliases.length ? aliases : [empty('尚無個人語意稱呼。')]));
  const evidence = list(data.evidence).map(item => {
    const node = el('details', 'panel evidence-card');
    return append(node,
      append(el('summary'), append(el('div'), el('h3', '', item.source), el('small', '', `${text(item.id)} · Version ${text(item.version)}`)), badge(item.trusted ? 'TRUSTED' : 'UNTRUSTED', item.trusted ? 'teal' : 'amber')),
      el('p', 'evidence-content', item.content),
    );
  });
  replace('#evidence-list', ...(evidence.length ? evidence : [empty('目前沒有原始證據。')]));
  const artifacts = list(data.artifacts).map(artifact => {
    const download = el('a', 'button secondary small', '下載 Markdown');
    download.href = `/api/artifact/${encodeURIComponent(artifact.id)}`;
    download.setAttribute('download', '');
    const node = el('div', 'panel memory-artifact'); node.dataset.testid = 'memory-artifact'; node.dataset.artifactId = artifact.id;
    const info = append(el('div', 'artifact-info'), el('p', '', artifact.id), el('code', '', `SHA256 · ${text(artifact.sha256)}`),
      append(el('div', 'metadata-row'), badge(artifact.verified ? 'STRUCTURE VERIFIED' : 'REVALIDATION REQUIRED', artifact.verified ? 'teal' : 'amber'), badge(artifact.factual_status || 'CLAIM'), el('span', '', `Version ${artifact.version || 1}`)),
      artifact.parent_artifact_id ? el('small', '', `Previous · ${artifact.parent_artifact_id}`) : null,
      artifact.superseded_by_revision ? el('small', '', `歷史版本 · 已由 ${artifact.superseded_by_revision} 接續`) : null);
    append(node, info, download);
    const current = list(data.tasks).some(task => task.status === 'COMPLETED' && task.artifact_id === artifact.id);
    if (current && artifact.revalidation_required) {
      const review = button('重新驗證修訂', 'button secondary small', async () => {
        if (node.querySelector('form')) return;
        setBusy(review, true, '讀取目前來源…');
        try {
          const data = await api(`/api/artifact/${encodeURIComponent(artifact.id)}/review?reference_date=${repairReference()}`);
          node.append(artifactReviewForm(artifact, data));
        } catch (error) { notify(`無法開始重新驗證：${error.message}`, 'error'); }
        finally { setBusy(review, false); }
      });
      review.dataset.testid = 'review-artifact'; node.append(review);
    }
    return node;
  });
  replace('#memory-artifacts', ...(artifacts.length ? artifacts : [empty('尚無已保存成果。')]));
  drawMemoryGraph(data);
}
function repairReference() {
  const today = new Intl.DateTimeFormat('sv-SE', { timeZone: 'Asia/Taipei' }).format(new Date());
  return [today, state.workspace?.reference_date || today].sort().at(-1);
}
function clearStaleContext() {
  state.retrieval = null; state.rounds = []; state.execution = null;
  renderRounds(); renderContext(); updateExecuteButton();
  $('#retrieval-status').textContent = 'STALE'; $('#retrieval-status').className = 'badge badge-amber';
  $('#stop-reason').textContent = '記憶已修正，請重新檢索目前版本。';
  replace('#intent-strip'); $('#clarification').hidden = true;
  $('#execution-status').textContent = 'STALE'; $('#execution-status').className = 'badge badge-amber';
  replace('#execution-summary', el('p', 'supporting-text', '記憶版本已變更；再次接續時會重新檢索。'));
  $('#artifact-content').textContent = '請從 Memory Explorer 下載目前成品版本。';
  $('#artifact-download').hidden = true; $('#model-call-details').hidden = true;
  $('#artifact-meta').textContent = '先前結果已從此檢視清除，歷史紀錄仍保存。';
}
async function memoryMutation(path, body, submit, message) {
  if (state.repairing || state.executing || state.retrieving) throw new Error('請等待目前操作完成後再修正記憶。');
  state.repairing = true; setBusy(submit, true, '儲存版本…');
  try {
    const result = await api(path, { ...body, reference_date: repairReference() });
    clearStaleContext();
    await refreshWorkspace(); await loadMemory(); await loadLiveDemo(); notify(message);
    return result;
  } finally { state.repairing = false; setBusy(submit, false); }
}
function field(label, control, id) {
  control.id = id; const title = el('label', '', label); title.htmlFor = id;
  return append(el('div', 'repair-field'), title, control);
}
function factRevisionForm(fact) {
  const form = el('form', 'memory-repair-form'); form.dataset.testid = 'fact-revision-form';
  const evidence = list(state.memory.evidence).filter(e => e.trusted);
  const source = el('select'); source.required = true;
  source.replaceChildren(...evidence.map(e => option(e.id, `${e.id} · ${e.source}`)));
  if (evidence.some(e => e.id === fact.evidence_ids?.[0])) source.value = fact.evidence_ids[0];
  const preview = el('pre', 'repair-source');
  const showSource = () => { preview.textContent = evidence.find(e => e.id === source.value)?.content || '沒有可信來源。'; };
  source.addEventListener('change', showSource); showSource();
  const content = el('textarea'); content.value = fact.content; content.required = true; content.maxLength = 4000; content.rows = 4;
  const error = el('p', 'repair-error'); error.setAttribute('role', 'alert');
  const save = el('button', 'button primary small', '保存記憶新版本'); save.type = 'submit'; save.disabled = !evidence.length;
  const cancel = button('取消', 'button secondary small', () => form.remove());
  append(form, el('p', 'supporting-text', '內容必須直接出現在所選來源。保存後，這個專案的成品需要重新驗證；舊記憶與完成里程碑仍保留。'),
    field('既有可信來源', source, `source-${fact.id}`), preview,
    field('修正內容', content, `content-${fact.id}`), error, append(el('div', 'repair-actions'), save, cancel));
  form.addEventListener('submit', async event => {
    event.preventDefault(); error.textContent = '';
    try { await memoryMutation(`/api/memory/facts/${encodeURIComponent(fact.id)}/revise`, { content: content.value, evidence_id: source.value }, save, '記憶新版本已保存；請重新驗證受影響成品。'); }
    catch (failure) { error.textContent = failure.message; }
  });
  return form;
}
function artifactReviewForm(artifact, review) {
  const form = el('form', 'memory-repair-form'); form.dataset.testid = 'artifact-review-form';
  const content = el('textarea'); content.value = review.draft; content.rows = 13; content.required = true; content.maxLength = 20000;
  const old = el('details', 'repair-history'); append(old, el('summary', '', '查看原成品內容'), el('pre', 'repair-source', artifact.content));
  const sources = el('details', 'repair-history'); append(sources, el('summary', '', '核對目前必要記憶與來源'),
    ...list(review.facts).map(f => el('p', '', `${f.kind} · ${f.id}\n${f.content}`)),
    ...list(review.evidence).map(e => el('pre', 'repair-source', `${e.id}\n${e.content}`)));
  const ack = el('input'); ack.type = 'checkbox'; ack.id = `ack-${artifact.id}`;
  const label = el('label', 'repair-ack'); label.htmlFor = ack.id;
  append(label, ack, el('span', '', '我已核對目前來源與交接文字。此驗證只檢查格式、目前目標及限制的完整性；內容仍為 CLAIM。'));
  const save = el('button', 'button primary small', '保存重新驗證版本'); save.type = 'submit'; save.disabled = true;
  ack.addEventListener('change', () => { save.disabled = !ack.checked; });
  const error = el('p', 'repair-error'); error.setAttribute('role', 'alert');
  append(form, el('p', 'supporting-text', '下方提供目前目標與限制的修訂草稿。請核對並編輯三項尚未執行的驗收步驟；儲存會保留原成品、SHA 與工作完成紀錄。'),
    old, sources, field('交接成品修訂', content, `revision-${artifact.id}`), label, error,
    append(el('div', 'repair-actions'), save, button('取消', 'button secondary small', () => form.remove())));
  form.addEventListener('submit', async event => {
    event.preventDefault(); error.textContent = '';
    try { await memoryMutation(`/api/artifact/${encodeURIComponent(artifact.id)}/revalidate`, { content: content.value, snapshot: review.snapshot, acknowledged: ack.checked }, save, '重新驗證版本已保存；原成品保留為歷史版本。'); }
    catch (failure) { error.textContent = failure.message; save.disabled = !ack.checked; }
  });
  return form;
}
const SVG_NS = 'http://www.w3.org/2000/svg';
function svgNode(tag, attributes = {}, content) {
  const node = document.createElementNS(SVG_NS, tag);
  Object.entries(attributes).forEach(([key, value]) => node.setAttribute(key, String(value)));
  if (content !== undefined) node.textContent = text(content);
  return node;
}
function drawMemoryGraph(data) {
  const relations = list(data.relations).slice(0, 20);
  if (!relations.length) { replace('#memory-graph', empty('目前沒有已保存的關聯。')); return; }
  const project = data.project || {};
  const lookup = new Map([
    [project.id, { label: project.name || project.id, color: '#6ee3cc' }],
    ...list(data.facts).map(fact => [fact.id, { label: `${fact.kind} · ${fact.id}`, color: '#8faef2' }]),
    ...list(data.aliases).map(alias => [alias.id, { label: alias.alias, color: '#bcacf3' }]),
    ...list(data.evidence).map(evidence => [evidence.id, { label: evidence.source, color: '#91bcce' }]),
  ]);
  const ids = [...new Set(relations.flatMap(relation => [relation.from, relation.to]).filter(Boolean))].slice(0, 18);
  const rootId = ids.includes(project.id) ? project.id : ids[0];
  const nodes = new Map();
  const width = 430, height = Math.max(260, Math.ceil((ids.length - 1) / 2) * 52 + 40);
  const svg = svgNode('svg', { viewBox: `0 0 ${width} ${height}`, role: 'img', 'aria-label': `${project.name || 'Project'} 已保存記憶關聯圖` });
  nodes.set(rootId, { x: 215, y: height / 2 });
  ids.filter(id => id !== rootId).forEach((id, index) => { nodes.set(id, { x: index % 2 ? 364 : 65, y: 30 + Math.floor(index / 2) * 52 }); });
  relations.forEach(relation => {
    const from = nodes.get(relation.from), to = nodes.get(relation.to);
    if (!from || !to) return;
    const line = svgNode('line', { x1: from.x, y1: from.y, x2: to.x, y2: to.y, stroke: '#365367', 'stroke-width': 1.3 });
    line.append(svgNode('title', {}, `${relation.from} · ${relation.type} · ${relation.to}`));
    svg.append(line);
  });
  nodes.forEach((position, id) => {
    const item = lookup.get(id) || { label: id, color: '#91bcce' };
    const group = svgNode('g');
    group.append(svgNode('circle', { cx: position.x, cy: position.y, r: id === rootId ? 13 : 7, fill: item.color, opacity: id === rootId ? 1 : 0.85 }));
    group.append(svgNode('title', {}, `${text(item.label)} · ${id}`));
    const label = text(item.label);
    group.append(svgNode('text', { x: position.x, y: position.y + 25, fill: '#adc3d6', 'text-anchor': 'middle', 'font-size': 12 }, label.length > 14 ? `${label.slice(0, 13)}…` : label));
    svg.append(group);
  });
  replace('#memory-graph', svg, append(el('div', 'graph-legend'), el('span', '', 'Project'), el('span', '', 'Fact'), el('span', '', 'Alias')));
}

async function retrieveStream(payload) {
  const response = await fetch('/api/retrieve/stream', { method: 'POST', headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' }, body: JSON.stringify(payload), credentials: 'same-origin' });
  if (!response.ok || !response.headers.get('content-type')?.includes('text/event-stream') || !response.body) throw new Error('即時串流目前不可用。');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '', result = null;
  $('#trace-source').textContent = 'LIVE SSE';
  $('#trace-source').className = 'badge badge-teal';
  function consume(block) {
    let type = 'message';
    const dataLines = [];
    block.split('\n').forEach(line => {
      if (line.startsWith('event:')) type = line.slice(6).trim();
      if (line.startsWith('data:')) dataLines.push(line.slice(5).trimStart());
    });
    if (!dataLines.length) return;
    const data = JSON.parse(dataLines.join('\n'));
    if (data.error) throw new Error(text(data.error));
    if (type === 'round') {
      const index = state.rounds.findIndex(round => round.round === data.round);
      if (index >= 0) state.rounds[index] = data;
      else state.rounds.push(data);
      renderRounds();
    } else if (type === 'result') result = data;
  }
  try {
    while (true) {
      const chunk = await reader.read();
      buffer = (buffer + decoder.decode(chunk.value || new Uint8Array(), { stream: !chunk.done })).replace(/\r\n/g, '\n');
      let boundary;
      while ((boundary = buffer.indexOf('\n\n')) !== -1) { consume(buffer.slice(0, boundary)); buffer = buffer.slice(boundary + 2); }
      if (chunk.done) break;
    }
    if (buffer.trim()) consume(buffer);
  } finally { reader.releaseLock(); }
  if (!result) throw new Error('串流未包含最終結果。');
  return result;
}
async function runRetrieval(event) {
  event.preventDefault();
  if (state.repairing) { notify('記憶版本正在儲存，請完成後再檢索。'); return; }
  if (state.retrieving || state.quickBusy || state.executing) return;
  notify('');
  const query = $('#query').value.trim();
  if (!query) { $('#query').focus(); return; }
  const payload = { query, budget: Number($('#budget').value), strategy: 'E' };
  if (state.workspace?.reference_date) payload.reference_date = state.workspace.reference_date;
  state.retrieving = true; state.rounds = []; state.retrieval = null; state.quickBudget = Number($('#budget').value); updateExecuteButton();
  $('#recovery-query').value = query;
  $('#trace-query').textContent = query;
  $('#stop-reason').textContent = '正在由低成本線索開始搜尋…';
  $('#clarification').hidden = true;
  $('#trace-source').textContent = 'CONNECTING SSE';
  $('#trace-source').className = 'badge badge-neutral';
  $('#retrieval-status').textContent = 'SEARCHING';
  $('#retrieval-status').className = 'badge badge-teal';
  $('#context-empty').hidden = false; $('#context-result').hidden = true;
  replace('#intent-strip', ...['TIME', 'TOPIC', 'ACTION', 'CONFIDENCE PROBABILITY'].map(label => append(el('div'), el('span', '', label), el('strong', '', label === 'CONFIDENCE PROBABILITY' ? 'UNKNOWN' : 'Parsing…'))));
  renderRounds(); navigate('workspace');
  const submit = $('[data-testid="run-retrieval"]');
  setBusy(submit, true, '正在找回脈絡…');
  try {
    let result;
    try { result = await retrieveStream(payload); }
    catch {
      // The regular endpoint is a local retrieval only, never a model call.
      $('#trace-source').textContent = 'SAVED REPLAY';
      $('#trace-source').className = 'badge badge-amber';
      result = await api('/api/retrieve', payload);
    }
    acceptRetrieval(result);
  } catch (error) {
    $('#retrieval-status').textContent = 'ERROR';
    $('#retrieval-status').className = 'badge badge-red';
    $('#stop-reason').textContent = error.message;
    notify(`檢索未完成：${error.message}`, 'error');
  } finally { state.retrieving = false; setBusy(submit, false); updateExecuteButton(); }
}
function acceptRetrieval(result) {
  state.retrieval = result;
  state.rounds = list(result.rounds);
  $('#trace-query').textContent = result.query || $('#query').value;
  $('#retrieval-status').textContent = result.status || 'UNKNOWN';
  $('#retrieval-status').className = `badge badge-${result.status === 'RESOLVED' ? 'teal' : 'amber'}`;
  const intent = result.intent || {};
  replace('#intent-strip', ...[['TIME', intent.time], ['TOPIC', intent.topic], ['ACTION', intent.action], ['CONFIDENCE PROBABILITY', result.confidence_probability === null || result.confidence_probability === undefined ? 'UNKNOWN' : percentage(result.confidence_probability)]].map(([label, value]) => append(el('div'), el('span', '', label), el('strong', '', value))));
  $('#stop-reason').textContent = result.stop_reason || 'UNKNOWN';
  $('#clarification').textContent = result.clarification ? compactText(result.clarification) : '';
  $('#clarification').hidden = !result.clarification;
  renderRounds(); renderContext(); updateExecuteButton();
  if (result.project_id && list(state.workspace?.projects).some(project => project.id === result.project_id)) {
    $('#memory-project').value = result.project_id;
    $('#memory-search').value = '';
    loadMemory();
  }
}
function renderRounds() {
  $('#round-count').textContent = `${state.rounds.length} rounds`;
  const current = state.rounds.at(-1);
  const tokenTotal = state.retrieval?.retrieval_tokens ?? current?.cumulative_tokens;
  $('#trace-token-total').textContent = `Local token estimate · ${fmt(tokenTotal)}`;
  const layerValue = current?.layer;
  const level = typeof layerValue === 'number' ? layerValue : Number(String(layerValue ?? '').replace('L', ''));
  $$('[data-layer]').forEach(node => {
    const reached = state.rounds.some(round => String(round.layer).replace('L', '') === node.dataset.layer);
    node.classList.toggle('reached', reached);
    node.classList.toggle('current', !!current && Number(node.dataset.layer) === level);
  });
  const cards = state.rounds.map(round => {
    const node = el('article', 'round-card'); node.dataset.testid = 'retrieval-round';
    const layer = String(round.layer ?? 'UNKNOWN').startsWith('L') ? round.layer : `L${round.layer}`;
    append(node, append(el('div', 'round-head'), el('h3', '', `Round ${round.round} · ${layer}`), el('span', 'muted numeric', `+${fmt(round.tokens)} / ${fmt(round.cumulative_tokens)} tokens`)), el('p', 'round-reason', round.reason));
    append(node, append(el('div', 'term-list'), ...list(round.search_terms).map(term => el('span', 'term', term))));
    const candidates = list(round.candidates).slice(0, 5).map(candidate => {
      const track = el('div', 'score-track'), fill = el('span');
      fill.style.width = knownNumber(candidate.score) ? `${Math.min(100, Math.max(0, candidate.score * 100))}%` : '0%';
      track.append(fill);
      return append(el('div', 'round-candidate'), el('span', '', candidate.name || candidate.project_id), track, el('strong', '', fmt(candidate.score, 3)));
    });
    append(node, append(el('div', 'round-candidates'), ...candidates));
    const clues = list(round.new_clues), information = list(round.new_information);
    if (clues.length || information.length) append(node, append(el('div', 'round-new'), el('h4', '', 'NEW CLUES & INFORMATION'), ...[...clues, ...information].map(item => el('p', '', compactText(item)))));
    return node;
  });
  replace('#retrieval-rounds', ...(cards.length ? cards : [empty(state.retrieving ? '正在探索第一個低成本線索…' : '檢索尚未開始。')]));
  renderCandidates(current?.candidates); drawCandidateChart();
}
function renderCandidates(candidates) {
  const labels = { time: 'Time', topic: 'Topic', alias: 'Alias', behavior: 'Behavior', content: 'Content', unfinished: 'Open work', frequency: 'Frequency' };
  const nodes = list(candidates).slice(0, 4).map(candidate => {
    const node = el('div', 'candidate-item');
    append(node, append(el('div', 'candidate-head'), el('h3', '', candidate.name || candidate.project_id), el('strong', '', fmt(candidate.score, 3))));
    const dimensions = Object.entries(labels).map(([key, label]) => append(el('span'), el('span', '', label), el('b', '', fmt(candidate.dimensions?.[key], 3))));
    append(node, append(el('div', 'candidate-dimensions'), ...dimensions));
    list(candidate.positive_evidence).forEach(item => append(node, el('p', 'candidate-evidence', `＋ ${compactText(item)}`)));
    list(candidate.negative_evidence).forEach(item => append(node, el('p', 'candidate-evidence negative', `− ${compactText(item)}`)));
    return node;
  });
  replace('#candidate-list', ...nodes);
}
const chartColors = ['#6ee3cc', '#8faef2', '#bcacf3', '#e1b781'];
function drawCandidateChart() {
  if (!state.rounds.length) { replace('#candidate-chart', empty('等待候選專案。')); return; }
  const ids = [...new Set(state.rounds.flatMap(round => list(round.candidates).map(candidate => candidate.project_id)))].slice(0, 4);
  const width = 410, height = 190, x0 = 37, y0 = 14, chartWidth = 353, chartHeight = 134;
  const svg = svgNode('svg', { viewBox: `0 0 ${width} ${height}`, role: 'img', 'aria-label': '各候選專案在每輪檢索的加權分數變化，分數不等於正確機率' });
  [0, 0.5, 1].forEach(value => {
    const y = y0 + chartHeight * (1 - value);
    svg.append(svgNode('line', { x1: x0, y1: y, x2: x0 + chartWidth, y2: y, stroke: '#293e51', 'stroke-dasharray': '3 5' }));
    svg.append(svgNode('text', { x: 25, y: y + 4, fill: '#859db2', 'font-size': 11, 'text-anchor': 'end' }, value.toFixed(1)));
  });
  state.rounds.forEach((round, index) => {
    const x = x0 + chartWidth * (state.rounds.length === 1 ? 0.5 : index / (state.rounds.length - 1));
    svg.append(svgNode('text', { x, y: 172, fill: '#859db2', 'font-size': 11, 'text-anchor': 'middle' }, `R${round.round}`));
  });
  const keys = el('div', 'chart-key');
  ids.forEach((id, index) => {
    const color = chartColors[index];
    const points = state.rounds.map((round, roundIndex) => {
      const candidate = list(round.candidates).find(item => item.project_id === id);
      if (!knownNumber(candidate?.score)) return null;
      return { x: x0 + chartWidth * (state.rounds.length === 1 ? 0.5 : roundIndex / (state.rounds.length - 1)), y: y0 + chartHeight * (1 - Math.min(1, Math.max(0, candidate.score))), score: candidate.score, name: candidate.name };
    }).filter(Boolean);
    if (!points.length) return;
    svg.append(svgNode('polyline', { points: points.map(point => `${point.x},${point.y}`).join(' '), fill: 'none', stroke: color, 'stroke-width': 2.2, 'stroke-linejoin': 'round' }));
    points.forEach(point => { const circle = svgNode('circle', { cx: point.x, cy: point.y, r: 3.5, fill: color }); circle.append(svgNode('title', {}, `${point.name || id} · ${fmt(point.score, 3)}`)); svg.append(circle); });
    const swatch = el('i'); swatch.style.background = color;
    keys.append(append(el('span'), swatch, el('span', '', points[0].name || id)));
  });
  replace('#candidate-chart', svg, keys);
}

function renderContext() {
  const context = state.retrieval?.context;
  if (!context) { $('#context-empty').hidden = false; $('#context-result').hidden = true; return; }
  $('#context-empty').hidden = true; $('#context-result').hidden = false;
  const coverage = knownNumber(context.coverage) ? percentage(context.coverage) : 'UNKNOWN';
  replace('#context-stats',
    metric('Known mandatory coverage', coverage, '已知必要記憶，不代表全部歷史'),
    metric('Context feasibility', context.feasible === true ? 'FEASIBLE' : context.feasible === false ? 'BLOCKED' : 'UNKNOWN', text(context.budget_status), true),
    metric('Packed context budget', fmt(context.token_breakdown?.total), `${fmt(Number($('#budget').value))} tokens available`),
    metric('Semantic page faults', fmt(list(context.faults).length), '補充讀取或阻止不完整執行'),
  );
  const categories = [
    ['system', 'System', '#8faef2'], ['user', 'User', '#9fc6d3'], ['mandatory', 'Mandatory', '#6ee3cc'], ['work', 'Work state', '#45aca4'],
    ['evidence', 'Evidence', '#bcacf3'], ['tools', 'Tools', '#7e94aa'], ['output_reserve', 'Output reserve', '#e1b781'], ['safety_margin', 'Safety margin', '#bd8c9c'],
  ];
  const total = context.token_breakdown?.total;
  const stack = categories.map(([key, , color]) => {
    const node = el('span');
    node.style.background = color;
    node.style.width = knownNumber(total) && total > 0 && knownNumber(context.token_breakdown?.[key]) ? `${context.token_breakdown[key] / total * 100}%` : '0%';
    node.title = `${key} · ${fmt(context.token_breakdown?.[key])}`;
    return node;
  });
  replace('#token-stack', ...stack);
  replace('#token-breakdown', ...categories.map(([key, label, color]) => {
    const node = el('div', 'token-category'); node.dataset.testid = 'token-category';
    const swatch = el('i'); swatch.style.background = color;
    return append(node, append(el('span'), swatch, el('span', '', label)), el('strong', 'numeric', fmt(context.token_breakdown?.[key])));
  }));
  const manifest = context.manifest || {};
  const manifestFields = [ ['active_task', 'Active task'], ['mandatory_memory', 'Mandatory memory'], ['required_dependencies', 'Required dependencies'], ['evidence_references', 'Evidence references'], ['missing_information', 'Missing information'], ['memory_snapshot', 'Memory snapshot'] ];
  replace('#memory-manifest', ...manifestFields.map(([key, label]) => append(el('div', 'manifest-row'), el('span', '', label), el('p', '', Array.isArray(manifest[key]) ? manifest[key].map(compactText).join('\n') || 'NONE RECORDED' : text(manifest[key])))));
  renderContextItems('#loaded-list', context.loaded, '尚無載入內容。');
  renderContextItems('#not-loaded-list', context.not_loaded, '沒有額外的未載入記憶。');
  renderContextItems('#missing-list', context.missing, '沒有已知缺失。');
  renderContextItems('#conflict-list', context.conflicts, '沒有未解決衝突。');
  renderContextItems('#fault-list', context.faults, '沒有記憶頁面缺失紀錄。');
  $('#loaded-count').textContent = `${list(context.loaded).length} items`;
  $('#not-loaded-count').textContent = `${list(context.not_loaded).length} items`;
}
function renderContextItems(selector, values, emptyMessage) {
  const nodes = list(values).map(value => {
    const node = el('div', 'context-item');
    if (value && typeof value === 'object') {
      const label = [value.kind || value.type, value.id || value.fact_id].filter(Boolean).join(' · ');
      if (label) node.append(el('strong', '', label));
      node.append(el('p', '', compactText(value)));
      const metadata = [value.version !== undefined ? `Version ${value.version}` : null, value.verification, value.trust !== undefined ? `Trust ${value.trust}` : null].filter(Boolean);
      if (metadata.length) node.append(el('small', '', metadata.join(' · ')));
    } else node.append(el('p', '', value));
    return node;
  });
  replace(selector, ...(nodes.length ? nodes : [empty(emptyMessage)]));
}

function renderModelSelection() {
  const mode = $('#execution-mode').value;
  const settings = state.workspace?.settings || {};
  const models = state.models || {};
  const catalog = list(mode === 'SMART' ? models.smart : models.fixed);
  const configuredModel = mode === 'SMART' ? settings.smart_model : settings.fixed_model;
  const ids = [...new Set([...catalog.map(item => typeof item === 'string' ? item : item.id), configuredModel].filter(Boolean))];
  const previous = $('#execution-model').value;
  if (mode === 'SIMULATION') {
    $('#execution-model').replaceChildren(option('', 'SIMULATION 不使用模型'));
    $('#execution-model').disabled = true;
    $('#execution-source').textContent = 'SIMULATION';
    $('#execution-source').className = 'badge badge-amber';
    $('#model-availability').textContent = '模擬執行使用真實持久化記憶，產生本機成果，不呼叫付費 API。';
  } else {
    $('#execution-model').replaceChildren(...(ids.length ? ids.map(id => option(id, id)) : [option('', '目前沒有已驗證的模型設定')]));
    if (ids.includes(previous)) $('#execution-model').value = previous;
    else if (ids.includes(configuredModel)) $('#execution-model').value = configuredModel;
    $('#execution-model').disabled = !ids.length;
    $('#execution-source').textContent = `LIVE · ${mode}`;
    $('#execution-source').className = 'badge badge-teal';
    $('#model-availability').textContent = `${settings.enabled || models.enabled ? '付費執行已啟用。' : '付費執行尚未啟用，後端會阻止呼叫。'}唯讀模型目錄不代表已授權路由模型池；實際呼叫仍由後端驗證。${models.error ? ` ${models.error}` : ''}`;
  }
  $('#workspace-model-status').textContent = settings.enabled || models.enabled ? `Live execution enabled · Fixed ${settings.fixed_model || 'UNKNOWN'} · Smart ${settings.smart_model || 'UNKNOWN'}` : 'Live execution disabled · 可先在 Recovery Lab 使用 SIMULATION。';
  updateExecuteButton();
}
function updateExecuteButton() {
  const mode = $('#execution-mode').value;
  const submit = $('#execute-task');
  const busy = state.executing || state.creatingSession || state.quickBusy;
  submit.disabled = busy || state.retrieving || state.repairing || !quickReady();
  $('#query').disabled = busy; $('#budget').disabled = busy; $('#execution-mode').disabled = busy;
  if (busy) $('#execution-model').disabled = true;
  const example = $('#quick-example'); if (example) example.disabled = busy;
  submit.textContent = busy ? '正在接續，請稍候…' : mode === 'SIMULATION' ? '確認專案，產生本機示範成果' : '確認專案，使用 MixRoute 接續';
  updateQuickSummary();
}
async function newSession() {
  if (state.executing || state.creatingSession) return;
  notify(''); state.creatingSession = true; updateExecuteButton();
  const node = $('#new-session'); setBusy(node, true, '建立獨立 Session…');
  try {
    const body = state.session ? { previous_session_id: state.session.id } : {};
    const session = await api('/api/session', body);
    state.session = session;
    $('#session-id').textContent = session.id;
    $('#session-history').textContent = text(session.raw_history_count);
    $('#session-badge').textContent = session.raw_history_count === 0 ? 'FRESH · NO RAW HISTORY' : 'HISTORY CHECK FAILED';
    $('#session-badge').className = `badge badge-${session.raw_history_count === 0 ? 'teal' : 'red'}`;
    if (session.raw_history_count !== 0) { state.session = null; throw new Error('新 Session 的原始對話數不為零，已阻止接續工作。'); }
    state.execution = null;
    $('#execution-status').textContent = 'READY'; $('#execution-status').className = 'badge badge-teal';
    replace('#execution-summary', el('p', 'supporting-text', `Session ${session.id} 已建立；原始對話數為 0。下一步將重新檢索持久化記憶。`));
    $('#artifact-content').textContent = '尚未產生成果。'; $('#artifact-download').hidden = true;
    $('#artifact-meta').textContent = '成果會由後端保存，包含內容雜湊與驗證狀態。';
    $('#model-call-details').hidden = true;
  } catch (error) { notify(`Session 建立失敗：${error.message}`, 'error'); }
  finally { state.creatingSession = false; setBusy(node, false); updateExecuteButton(); }
}

function quickReady() {
  const r = state.retrieval;
  const completed = r?.context?.budget_status === 'FEASIBLE' && list(r.context?.missing).length === 1 && r.context.missing[0] === '沒有可接續的未完成任務' && list(state.workspace?.tasks).some(t => t.project_id === r.project_id && t.status === 'COMPLETED' && t.artifact_id);
  return r?.status === 'RESOLVED' && (r.context?.feasible === true || completed) &&
    r.query?.trim() === $('#query').value.trim() && state.quickBudget === Number($('#budget').value);
}
function updateQuickSummary() {
  const node = $('#quick-context'); if (!node) return;
  const r = state.retrieval;
  if (!quickReady()) {
    node.replaceChildren(el('p', 'supporting-text', state.retrieving ? '正在找回專案、目標與限制…' : r?.clarification ? compactText(r.clarification) : '先找回記憶；若修改需求或預算，請重新搜尋後再接續。'));
    return;
  }
  const loaded = list(r.context.loaded);
  const parts = loaded.filter(f => ['GOAL', 'CONSTRAINT'].includes(f.kind));
  node.replaceChildren(el('h3', '', `找到專案：${projectName(r.project_id)}`),
    ...parts.map(f => el('p', 'supporting-text', `${f.kind === 'GOAL' ? '目標' : '限制'}：${f.content}`)),
    el('p', 'supporting-text', r.context.feasible ? '必要記憶已備妥。請確認這是你要接續的專案；按下接續後會自動建立空白對話。' : '此專案沒有未完成任務，將取回已保存成果，不新增模型呼叫。'));
}
async function executeTask(event) {
  event.preventDefault();
  if (state.quickBusy || state.executing || state.creatingSession || state.repairing || !quickReady()) return;
  const confirmed = { query: $('#query').value.trim(), budget: $('#budget').value, mode: $('#execution-mode').value, model: $('#execution-model').value };
  state.quickBusy = true; updateExecuteButton();
  try {
    const previous = state.session?.id;
    await newSession();
    if (!state.session || state.session.id === previous || state.session.raw_history_count !== 0) return;
    if (!quickReady() || confirmed.query !== $('#query').value.trim() || confirmed.budget !== $('#budget').value || confirmed.mode !== $('#execution-mode').value || confirmed.model !== $('#execution-model').value) { notify('確認內容已改變，請重新找回記憶後再接續。'); return; }
    $('#recovery-query').value = confirmed.query;
    await performExecution({ preventDefault() {} });
    $('#quick-output').scrollIntoView({ block: 'start', behavior: 'smooth' });
  } finally { state.quickBusy = false; renderModelSelection(); }
}
function mountQuickFlow() {
  const main = $('#view-workspace .workspace-main');
  const flow = el('div', 'quick-flow');
  const confirm = el('section', 'panel quick-confirm');
  confirm.append(el('h2', '', '2 · 確認找到的專案'));
  const summary = el('div'); summary.id = 'quick-context'; confirm.append(summary, $('#execution-form'));
  const output = el('section'); output.id = 'quick-output';
  output.append(el('h2', '', '3 · 取得成果'), $('.recovery-output'));
  flow.append(confirm, output); main.insertBefore(flow, $('#retrieval-form').nextSibling);
  $('#recovery-query').closest('label').hidden = true;
  $('#workspace-title').textContent = '把上次的工作，接著做好。';
  $('#view-workspace .page-description').textContent = '輸入需求 → 確認專案 → 取得成果。先試試已準備好的鋼琴教材情境。';
  $('#retrieval-form h2').textContent = '1 · 輸入你想接續的工作';
  $('#query').value = '請接續鋼琴樂理教材，完成目前尚未完成的驗收清單。';
  const example = button('填入鋼琴教材範例', 'text-button', () => { $('#query').value = '請接續鋼琴樂理教材，完成目前尚未完成的驗收清單。'; updateExecuteButton(); $('#query').focus(); });
  example.id = 'quick-example'; $('#retrieval-form').insertBefore(example, $('#query'));
  $('#execution-form .section-top h2').textContent = '選擇接續方式';
  $('#execution-form .supporting-text').textContent = 'SMART／FIXED 會使用真實 MixRoute API 額度；本機示範不呼叫模型。已完成的任務會讀取既有成果。';
  const details = el('details'); details.append(el('summary', '', '模型、Token 與請求明細'), $('#model-call-details')); $('#execution-summary').after(details);
  const advanced = el('details', 'quick-advanced'); advanced.append(el('summary', '', '查看專案與活動（進階）'));
  [...main.children].filter(n => n !== $('#retrieval-form') && n !== flow).forEach(n => advanced.append(n)); main.append(advanced);
  $('#query').addEventListener('input', updateExecuteButton);
  $('#budget').addEventListener('change', updateExecuteButton);
  updateExecuteButton();
}

async function performExecution(event) {
  event.preventDefault();
  if (state.repairing) { notify('記憶版本正在儲存，請完成後再接續工作。'); return; }
  if (!state.session || state.executing) return;
  const query = $('#recovery-query').value.trim();
  if (!query) { $('#recovery-query').focus(); return; }
  notify('');
  const mode = $('#execution-mode').value;
  // A unique identifier for this explicit attempt. The backend owns delivery
  // deduplication across sessions and immutable artifact transactions.
  const idempotencyKey = globalThis.crypto?.randomUUID ? crypto.randomUUID() : `attempt-${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const payload = { query, budget: Number($('#budget').value), mode, idempotency_key: idempotencyKey, session_id: state.session.id };
  if (state.workspace?.reference_date) payload.reference_date = state.workspace.reference_date;
  if (mode !== 'SIMULATION' && $('#execution-model').value) payload.model = $('#execution-model').value;
  state.executing = true; updateExecuteButton();
  $('#new-session').disabled = true; $('#execution-mode').disabled = true; $('#execution-model').disabled = true;
  $('#execution-status').textContent = 'RUNNING'; $('#execution-status').className = 'badge badge-teal';
  try {
    const result = await api('/api/execute', payload);
    state.execution = result;
    renderExecution(result);
    if (result.retrieval) {
      $('#trace-source').textContent = 'SAVED REPLAY'; $('#trace-source').className = 'badge badge-amber';
      acceptRetrieval(result.retrieval);
    }
    await refreshWorkspace();
  } catch (error) {
    $('#execution-status').textContent = 'ERROR'; $('#execution-status').className = 'badge badge-red';
    replace('#execution-summary', el('p', 'execution-info', error.message));
    notify(`工作未完成：${error.message}`, 'error');
  } finally {
    state.executing = false; $('#new-session').disabled = false; $('#execution-mode').disabled = false;
    renderModelSelection();
  }
}
function renderExecution(result) {
  const completed = ['COMPLETED', 'ALREADY_COMPLETED'].includes(result.status);
  $('#execution-status').textContent = result.status || 'UNKNOWN';
  $('#execution-status').className = `badge badge-${completed ? 'teal' : 'amber'}`;
  const summary = el('div', 'execution-info');
  append(summary, badge(result.mode === 'SIMULATION' ? 'SIMULATION · LOCAL ARTIFACT' : `LIVE · ${result.mode}`, result.mode === 'SIMULATION' ? 'amber' : 'teal'), el('p', '', `Project · ${projectName(result.project_id)}`));
  if (result.reason) append(summary, el('p', '', result.reason));
  if (result.status === 'ALREADY_COMPLETED') append(summary, el('p', '', '已找到先前完成的成果，本次沒有重複交付。'));
  append(summary, el('p', 'supporting-text', `Session · ${text(result.session_id)} · Elapsed ${fmt(result.elapsed_ms)} ms`));
  replace('#execution-summary', summary);
  const artifact = result.artifact;
  if (artifact) {
    $('#artifact-content').textContent = text(artifact.content);
    $('#artifact-meta').textContent = `${result.mode === 'SIMULATION' ? 'SIMULATION · ' : ''}${artifact.verified ? 'STRUCTURE VERIFIED' : 'UNVERIFIED'} · ${artifact.id}\nSHA256 · ${text(artifact.sha256)}`;
    $('#artifact-download').href = `/api/artifact/${encodeURIComponent(artifact.id)}`;
    $('#artifact-download').setAttribute('download', '');
    $('#artifact-download').hidden = false;
  } else {
    $('#artifact-content').textContent = completed ? '後端未提供成果內容。' : '尚未交付成果；請先處理執行阻擋原因。';
    $('#artifact-download').hidden = true;
    $('#artifact-meta').textContent = 'No artifact returned';
  }
  const call = result.model_call;
  $('#model-call-details').hidden = false;
  const values = [
    ['Actual model', call?.model || 'UNKNOWN'], ['Requested model', call?.requested_model || 'UNKNOWN'],
    ['Input tokens', fmt(call?.input_tokens)], ['Output tokens', fmt(call?.output_tokens)], ['Total API tokens', fmt(call?.total_tokens)],
    ['API cost', money(call?.cost_usd)], ['Cost source', call?.cost_source || 'UNKNOWN'], ['Model latency', knownNumber(call?.latency_ms) ? `${fmt(call.latency_ms)} ms` : 'UNKNOWN'], ['Request ID', call?.request_id || 'UNKNOWN'],
  ];
  replace('#model-call-details', ...values.map(([label, value]) => append(el('div', 'call-stat'), el('span', '', label), el('strong', '', value))));
}

async function runBenchmark(event) {
  event.preventDefault(); notify('');
  const budgets = $$('input[name="benchmark-budget"]:checked').map(node => Number(node.value));
  const strategies = $$('input[name="benchmark-strategy"]:checked').map(node => node.value);
  if (!budgets.length || !strategies.length) { notify('請至少選擇一個 Token 預算與一種比較策略。'); return; }
  const submit = $('#run-benchmark');
  if (submit.disabled) return;
  setBusy(submit, true, '正在量測離線檢索…');
  $('#benchmark-mode').textContent = 'RUNNING · OFFLINE RETRIEVAL';
  try {
    const result = await api('/api/benchmark', { count: Number($('#benchmark-count').value), budgets, strategies, live: false });
    state.benchmark = result; renderBenchmark(result); await refreshWorkspace();
  } catch (error) { $('#benchmark-mode').textContent = 'ERROR'; notify(`Benchmark 未完成：${error.message}`, 'error'); }
  finally { setBusy(submit, false); }
}
function renderBenchmark(result) {
  const rows = list(result.results);
  if (!rows.length) return;
  $('#benchmark-mode').textContent = `${result.mode || 'UNKNOWN'} · ${fmt(result.elapsed_ms)} ms`;
  if (result.id) { $('#benchmark-export').href = `/api/export/${encodeURIComponent(result.id)}`; $('#benchmark-export').setAttribute('download', ''); $('#benchmark-export').hidden = false; }
  const charts = el('div', 'benchmark-chart-grid');
  charts.append(drawComparisonBars(rows, 'top1_accuracy', 'Project identification', 'Top-1 accuracy · same selected context budgets', percentage));
  charts.append(drawComparisonBars(rows, 'critical_memory_recall', 'Critical memory recall', 'Known mandatory memory recovered', percentage));
  const columns = [
    ['strategy', 'STRATEGY', value => text(value)], ['budget', 'BUDGET', value => `${fmt(value / 1024)}K`], ['cases', 'CASES', fmt],
    ['top1_accuracy', 'TOP-1', percentage], ['top3_accuracy', 'TOP-3', percentage], ['mrr', 'MRR', value => fmt(value, 3)],
    ['critical_memory_recall', 'CRITICAL RECALL', percentage], ['memory_precision', 'PRECISION', percentage], ['task_success_rate', 'TASK SUCCESS', percentage],
    ['critical_constraint_omission_rate', 'CONSTRAINT OMISSION', percentage], ['wrong_project_execution_rate', 'WRONG EXECUTION', percentage],
    ['unnecessary_clarification_rate', 'UNNEEDED CLARIFY', percentage], ['duplicate_completed_rate', 'DUPLICATE COMPLETION', percentage],
    ['mean_rounds', 'MEAN ROUNDS', value => fmt(value, 2)], ['mean_retrieval_tokens', 'RETRIEVAL TOKENS', value => fmt(value, 1)],
    ['mean_context_tokens_estimate', 'CONTEXT · EST.', value => fmt(value, 1)], ['mean_e2e_tokens', 'E2E · ACTUAL', value => fmt(value, 1)], ['api_cost_usd', 'API COST', money], ['mean_latency_ms', 'LATENCY · MS', value => fmt(value, 1)],
    ['cost_per_success', 'COST / SUCCESS', money], ['status', 'STATUS', value => text(value)],
  ];
  const table = el('table');
  table.setAttribute('aria-label', '實際後端 Benchmark 結果，未量測欄位為 UNKNOWN');
  table.append(append(el('thead'), append(el('tr'), ...columns.map(([, label]) => { const node = el('th', '', label); node.scope = 'col'; return node; }))));
  const body = el('tbody');
  rows.forEach(row => {
    const tr = el('tr', row.strategy === 'E' ? 'highlight' : ''); tr.dataset.testid = 'benchmark-row';
    columns.forEach(([key, , formatter]) => {
      const value = row[key] === null || row[key] === undefined ? 'UNKNOWN' : formatter(row[key]);
      tr.append(el('td', key === 'status' ? 'status-cell' : value === 'UNKNOWN' ? 'unknown' : 'numeric', value));
    });
    body.append(tr);
  });
  table.append(body);
  const panel = append(el('div', 'panel table-panel'), append(el('div', 'table-caption'), el('span', '', `${rows.length} result rows · ${text(result.id)}`), el('span', '', '橫向捲動查看全部指標')), append(el('div', 'table-scroll'), table), el('p', 'benchmark-results-note', 'UNKNOWN 表示沒有可用的實測值。離線檢索 Token 為本機估算；F 組需要真實 Smart Routing。'));
  replace('#benchmark-results', charts, panel);
  const limits = list(result.limits);
  $('#benchmark-limits').hidden = !limits.length;
  $('#benchmark-limits').replaceChildren(...limits.map(limit => el('p', '', compactText(limit))));
}
function drawComparisonBars(rows, key, title, description, formatter) {
  const panel = append(el('div', 'panel benchmark-chart'), el('h2', '', title), el('p', 'supporting-text', description));
  const measured = rows.filter(row => knownNumber(row[key]));
  if (!measured.length) { panel.append(empty('UNKNOWN · 尚未量測')); return panel; }
  const bars = el('div', 'comparison-bars');
  measured.forEach(row => {
    const track = el('div', 'bar-track'), fill = el('span');
    fill.style.width = `${Math.min(100, Math.max(0, row[key] * 100))}%`; track.append(fill);
    bars.append(append(el('div', `comparison-bar${row.strategy === 'E' ? ' highlight' : ''}`), el('span', '', `${row.strategy} · ${fmt(row.budget / 1024)}K`), track, el('strong', '', formatter(row[key]))));
  });
  panel.append(bars); return panel;
}
async function refreshWorkspace() {
  try { const data = await api('/api/state'); if (Array.isArray(data.projects)) { state.workspace = data; renderWorkspace(data); } }
  catch (error) { notify(`最新資源資料未能重新載入：${error.message}`, 'error'); }
}
async function loadLiveDemo() {
  try {
    state.liveDemo = await api('/api/demo'); renderLiveDemo();
    if (!state.demoBusy && list(state.liveDemo.stages).some(stage => stage.status === 'COMPLETED')) $('#demo-message').textContent = '目前顯示已保存紀錄；重新載入不會新增模型呼叫。';
  }
  catch (error) { $('#demo-message').textContent = `示範尚未載入：${error.message}`; }
}
function renderLiveDemo() {
  const data = state.liveDemo;
  if (!data) return;
  const enabled = !!state.workspace?.settings?.enabled;
  $('#demo-mode').querySelector('option[value="LIVE"]').disabled = !enabled;
  if (!enabled) $('#demo-mode').value = 'SIMULATION';
  $('#demo-prepare').textContent = data.prepared ? '讀取已保存示範' : '準備合成交接專案';
  $('#demo-prepare').disabled = state.demoBusy;
  $('#demo-mode').disabled = state.demoBusy;
  const stages = list(data.stages), one = stages[0], two = stages[1];
  $('#demo-stage-1').disabled = state.demoBusy || !data.prepared || one?.status === 'COMPLETED';
  $('#demo-stage-2').disabled = state.demoBusy || one?.status !== 'COMPLETED' || !one?.artifact?.verified || two?.status === 'COMPLETED';
  const cards = stages.map((stage, index) => {
    const node = el('article', 'demo-stage-card'); node.dataset.testid = 'demo-stage-card';
    const call = stage.model_call, artifact = stage.artifact;
    append(node, append(el('div', 'section-top'), el('h3', '', `階段 ${index + 1} · ${stage.title}`), badge(stage.status, stage.status === 'COMPLETED' ? 'teal' : 'neutral')));
    if (!artifact) return append(node, el('p', 'supporting-text', index ? '等待前一階段的真實成品。' : '準備以空白 Session 取得持久化記憶。'));
    append(node, append(el('div', 'metadata-row'), badge(stage.mode || 'UNKNOWN', stage.mode === 'SIMULATION' ? 'amber' : 'teal'), badge('SAVED RECORD'), badge(artifact.factual_status || 'CLAIM')),
      el('p', 'demo-model', `實際模型 · ${call?.model || (stage.mode === 'SIMULATION' ? '本機工具' : 'UNKNOWN')}`),
      el('p', 'supporting-text', `要求模型 ${call?.requested_model || 'NONE'} · 原始歷史 ${text(stage.raw_history_count)} · 已知 Token ${fmt(call?.total_tokens)} · API 耗時 ${fmt(call?.latency_ms)} ms`),
      el('small', '', `實際費用 ${money(call?.cost_usd)} · 保守用量上界 ${money(call?.cost_upper_bound_usd)}（上界不是帳單）`),
      el('code', 'demo-request-id', `請求識別 · ${call?.request_id || call?.response_id || 'UNKNOWN'}`),
      el('code', 'demo-request-id', `Session · ${stage.session_id || 'UNKNOWN'}`),
      el('code', 'demo-request-id', `SHA256 · ${artifact.sha256}`));
    const details = el('details'); append(details, el('summary', '', '查看保存的成品'), el('pre', 'artifact-content', artifact.content));
    const download = el('a', 'button secondary small', '下載成品'); download.href = `/api/artifact/${encodeURIComponent(artifact.id)}`; download.setAttribute('download', '');
    return append(node, details, download);
  });
  replace('#demo-results', ...cards);
  const proof = two?.handoff_proof;
  if (proof?.prior_artifact_loaded) {
    const details = el('details'); append(details, el('summary', '', '查看第二模型收到的前一成品'), el('pre', 'artifact-content', proof.prior_content));
    replace('#demo-proof', badge('前一成品內容已載入', 'teal'), el('p', 'supporting-text', '前一成品的完整內容與 SHA 已在第二階段模型上下文核對；這是記憶交接證據，生成文字仍為 CLAIM。'), el('code', '', proof.prior_sha256), details);
  } else replace('#demo-proof');
  if (stages.some(stage => stage.status === 'COMPLETED') && !state.demoBusy) $('#demo-source').textContent = 'SAVED LIVE / SIMULATION RECORDS';
}
async function prepareLiveDemo() {
  if (state.demoBusy) return;
  state.demoBusy = true; renderLiveDemo();
  try { state.liveDemo = await api('/api/demo/prepare', {}); $('#demo-message').textContent = '資料已準備；保存紀錄與預算帳本保持原狀。'; await refreshWorkspace(); }
  catch (error) { $('#demo-message').textContent = error.message; }
  finally { state.demoBusy = false; renderLiveDemo(); }
}
async function runLiveDemo(stage) {
  if (state.demoBusy || state.repairing || state.executing || state.retrieving) return;
  const local = $('#demo-mode').value === 'SIMULATION';
  const mode = local ? 'SIMULATION' : stage === 1 ? 'SMART' : 'FIXED';
  state.demoBusy = true; renderLiveDemo();
  $('#demo-source').textContent = local ? 'SIMULATION · NO API' : 'LIVE · MIXROUTE';
  $('#demo-message').textContent = `正在執行第 ${stage} 階段 · ${mode}。${local ? '本機工具產生清單。' : '呼叫實際 API，請等待回傳。'}`;
  try {
    const result = await api('/api/demo/run', { stage, mode, idempotency_key: crypto.randomUUID() });
    if (!['COMPLETED', 'ALREADY_COMPLETED'].includes(result.status)) throw new Error(result.reason || result.status);
    state.execution = result; renderExecution(result);
    if (result.retrieval) acceptRetrieval(result.retrieval);
    await refreshWorkspace(); await loadLiveDemo();
    $('#demo-message').textContent = `${stage === 1 ? '第一' : '第二'}階段完成 · ${result.mode} · ${result.stored_replay ? '保存紀錄，沒有新增呼叫' : local ? '本機成果，沒有 API 呼叫' : '新 LIVE 成品已保存'}。`;
  } catch (error) { $('#demo-message').textContent = `階段未完成：${error.message}`; }
  finally { state.demoBusy = false; renderLiveDemo(); }
}
async function boot() {
  const results = await Promise.allSettled([api('/api/state'), api('/api/models'), api('/api/benchmark/latest')]);
  const [workspace, models, benchmark] = results;
  if (models.status === 'fulfilled') state.models = models.value;
  if (workspace.status === 'fulfilled' && Array.isArray(workspace.value.projects) && workspace.value.dataset) {
    state.workspace = workspace.value; renderWorkspace(workspace.value); if (state.workspace.settings?.enabled) { $('#execution-mode').value = 'SMART'; renderModelSelection(); }
    $('[data-testid="backend-status"]').textContent = 'CONNECTED';
    $('[data-testid="backend-status"]').className = 'connection connected';
    loadMemory();
  } else {
    const reason = workspace.status === 'rejected' ? workspace.reason.message : '這個服務未提供 RE:MEMORY 資料契約。';
    $('[data-testid="backend-status"]').textContent = 'DISCONNECTED';
    $('[data-testid="backend-status"]').className = 'connection error';
    replace('#project-list', empty('無法讀取專案，請確認本機後端。'));
    replace('#activity-list', empty('無法讀取活動。'));
    replace('#open-tasks', empty('無法讀取工作。'));
    notify(`後端連線失敗：${reason}`, 'error');
  }
  if (models.status === 'rejected') { state.models = { error: models.reason.message }; renderModelSelection(); }
  if (benchmark.status === 'fulfilled' && list(benchmark.value.results).length) { state.benchmark = benchmark.value; renderBenchmark(benchmark.value); }
  await loadLiveDemo();
}
$$('[data-view]').forEach(node => node.addEventListener('click', () => navigate(node.dataset.view)));
$$('[data-go]').forEach(node => node.addEventListener('click', () => navigate(node.dataset.go)));
window.addEventListener('hashchange', () => navigate(location.hash.slice(1), false));
$('#retrieval-form').addEventListener('submit', runRetrieval);
$('#memory-search-form').addEventListener('submit', event => { event.preventDefault(); loadMemory(); });
$('#memory-project').addEventListener('change', () => { $('#memory-search').value = ''; loadMemory(); });
$$('[data-kind]').forEach(node => node.addEventListener('click', () => {
  state.kind = node.dataset.kind;
  $$('[data-kind]').forEach(item => item.classList.toggle('active', item === node));
  renderMemory();
}));
$('#execution-mode').addEventListener('change', renderModelSelection);
$('#new-session').addEventListener('click', newSession);
$('#execution-form').addEventListener('submit', executeTask);
$('#benchmark-form').addEventListener('submit', runBenchmark);
$('#demo-prepare').addEventListener('click', prepareLiveDemo);
$('#demo-stage-1').addEventListener('click', () => runLiveDemo(1));
$('#demo-stage-2').addEventListener('click', () => runLiveDemo(2));
$('#budget').addEventListener('change', () => { $('#recovery-budget').textContent = `${fmt(Number($('#budget').value) / 1024)}K tokens`; });
mountQuickFlow();
navigate(location.hash.slice(1) || 'workspace', false);
boot();
