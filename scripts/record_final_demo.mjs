// Genuine browser recording of persisted LIVE results. No paid generation or voice.
import {loadPlaywright,browserLaunchOptions} from './playwright_runtime.mjs';
import {mkdirSync,renameSync,writeFileSync} from 'node:fs';
const {chromium}=loadPlaywright();
const base=process.env.REMEMORY_BASE_URL||'http://127.0.0.1:8791';
const directory='reports/private/recording';mkdirSync(directory,{recursive:true});
const before=await(await fetch(base+'/api/state')).json();
const demo=await(await fetch(base+'/api/demo')).json();
if(demo.stages.length!==2||demo.stages.some(s=>s.status!=='COMPLETED'||!s.model_call))throw Error('Two persisted LIVE stages are required.');
const browser=await chromium.launch(browserLaunchOptions());
const context=await browser.newContext({viewport:{width:1440,height:900},recordVideo:{dir:directory,size:{width:1440,height:900}}});
const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
const started=Date.now();
async function at(second){await new Promise(r=>setTimeout(r,Math.max(0,second*1000-(Date.now()-started))));}
async function view(name){await page.locator(`[data-view="${name}"]`).click();}
try{
 await page.goto(base);await page.locator('[data-testid="backend-status"]').filter({hasText:'CONNECTED'}).waitFor();
 console.log('Recording 0–20s: actual workspace.');
 await at(20);await page.locator('#query').fill('請接續記憶交接示範專案');await page.locator('#budget').selectOption('4096');await page.locator('[data-testid="run-retrieval"]').click();
 await page.locator('[data-testid="retrieval-round"]').first().waitFor();await view('observatory');
 console.log('Recording 20–45s: actual local retrieval, no model call.');
 await at(45);await view('context');
 await at(55);await page.locator('[data-testid="context-result"]').scrollIntoViewIfNeeded();
 await at(65);await view('recovery');await page.locator('#live-demo-panel').scrollIntoViewIfNeeded();
 console.log('Recording 65–95s: saved SMART/auto Sonnet and Fixed DeepSeek results.');
 await at(78);await page.locator('#demo-results details').first().locator('summary').click();
 await at(86);await page.locator('#demo-results details').first().locator('summary').click();
 await at(95);await page.locator('#demo-proof details summary').click();await page.locator('#demo-proof').scrollIntoViewIfNeeded();
 console.log('Recording 95–120s: exact persisted prior content in second model context.');
 await at(109);await page.locator('#demo-proof details summary').click();await page.locator('#live-demo-panel').scrollIntoViewIfNeeded();
 await at(120);await view('benchmark');await page.locator('[data-testid="benchmark-row"]').first().waitFor();
 await at(130);await page.locator('[data-testid="benchmark-results"]').scrollIntoViewIfNeeded();
 await at(140);await view('workspace');await at(150);
}finally{
 const video=page.video();await context.close();renameSync(await video.path(),directory+'/RE-MEMORY-screen-silent.webm');await browser.close();
}
const after=await(await fetch(base+'/api/state')).json();
if(after.resources.api_calls!==before.resources.api_calls||errors.length)throw Error('Recording must add zero model calls and have no browser errors.');
writeFileSync(directory+'/capture.json',JSON.stringify({mode:'GENUINE_BROWSER_CAPTURE_OF_STORED_LIVE_RECORDS',human_voice_added:false,wall_seconds:(Date.now()-started)/1000,added_api_calls:0,actual_models:demo.stages.map(s=>s.model_call.model),errors},null,2));
console.log('PASS: 150-second genuine capture, two stored LIVE models, no extra API call or browser error; human voice pending.');
