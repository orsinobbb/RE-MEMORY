// A late project response must never redirect the next message into another scope.
import assert from 'node:assert/strict';
import {loadPlaywright,browserLaunchOptions} from '../scripts/playwright_runtime.mjs';
const base='http://127.0.0.1:8793';const marker=Date.now();
const projects=(await(await fetch(base+'/api/state')).json()).projects.slice(0,2);
async function create(p,index){
 const c=await(await fetch(base+'/api/chat/conversations',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project_id:p.id})})).json();
 await fetch(base+`/api/chat/conversations/${c.id}/messages`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:`範圍${index} ${marker}`,idempotency_key:`prepare-${index}-${marker}`})});
 return c;
}
const [c1,c2]=[await create(projects[0],1),await create(projects[1],2)];
const browser=await loadPlaywright().chromium.launch(browserLaunchOptions());
const page=await browser.newPage();page.setDefaultTimeout(5000);
try{
 await page.goto(base+'/');await page.locator('#chat-content').waitFor();
 await page.waitForFunction(()=>document.querySelector('#chat-project').options.length>2);
 let release;const gate=new Promise(r=>release=r);let entered;const started=new Promise(r=>entered=r);
 await page.route('**/api/chat?*',async route=>{
   if(new URL(route.request().url()).searchParams.get('project_id')===projects[0].id){entered();await gate;}
   await route.continue();
 });
 await page.locator('#chat-project').selectOption(projects[0].id);await started;
 await page.locator('#chat-project').selectOption(projects[1].id);
 await page.locator('#chat-conversation-title').filter({hasText:`範圍2 ${marker}`}).waitFor();
 const late=page.waitForResponse(r=>r.url().includes('/api/chat?')&&new URL(r.url()).searchParams.get('project_id')===projects[0].id);
 release();await late;await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
 assert.equal(await page.locator('#chat-conversation-title').innerText(),`範圍2 ${marker}`);
 const reply=page.waitForResponse(r=>r.url().includes('/messages')&&r.request().method()==='POST');
 await page.locator('#chat-content').fill(`第二範圍的訊息 ${marker}`);await page.locator('#chat-send').click();
 const result=await reply;assert.equal(new URL(result.url()).pathname,`/api/chat/conversations/${c2.id}/messages`);
 await page.locator('#chat-send').filter({hasText:'傳送訊息'}).waitFor();
 const failed=page.waitForResponse(r=>r.url().includes('/messages')&&r.request().method()==='POST');
 await page.locator('#chat-content').fill('FAIL_PAID_SYNTHETIC');await page.locator('#chat-send').click();
 assert.equal((await(await failed).json()).status,'FAILED');
 await page.locator('#chat-usage').filter({hasText:'UNKNOWN Token'}).waitFor();
 const other=await(await fetch(base+`/api/chat/conversations/${c1.id}`)).json();
 assert.equal(other.messages.length,2,'No message may be added to the former project.');
 assert.equal(await page.locator('[data-testid="dataset-label"]').innerText(),'本機聊天資料');
 console.log('PASS: late scope responses ignored, send stays in selected conversation, real chat label.');
}finally{await browser.close();}
