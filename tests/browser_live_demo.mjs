import assert from 'node:assert/strict';
import {loadPlaywright,browserLaunchOptions} from '../scripts/playwright_runtime.mjs';
const pw=loadPlaywright();
const url=process.env.REMEMORY_BASE_URL||'http://127.0.0.1:8792';
const initial=await(await fetch(url+'/api/state')).json();
assert.equal(initial.settings.enabled,false,'Run this workflow only on a live-disabled disposable fixture.');
const browser=await pw.chromium.launch(browserLaunchOptions());
const page=await browser.newPage({viewport:{width:1440,height:1000}});page.setDefaultTimeout(10000);
const errors=[];page.on('pageerror',e=>errors.push(e.message));
try{
 await page.goto(url+'/#recovery');
 await page.locator('[data-testid="backend-status"]').filter({hasText:'CONNECTED'}).waitFor();
 await page.locator('#demo-prepare').click();
 await page.locator('#demo-stage-1').waitFor();
 await page.waitForFunction(()=>!document.querySelector('#demo-stage-1').disabled);
 assert.equal(await page.locator('#demo-stage-2').isDisabled(),true);
 await page.locator('#demo-stage-1').click();
 await page.locator('#demo-message').filter({hasText:'第一階段完成'}).waitFor();
 assert.match(await page.locator('#demo-results').textContent(),/SIMULATION/);
 await page.locator('#demo-stage-2').click();
 await page.locator('#demo-message').filter({hasText:'第二階段完成'}).waitFor();
 assert.match(await page.locator('#demo-proof').textContent(),/前一成品內容已載入/);
 assert.equal(await page.locator('[data-testid="demo-stage-card"]').count(),2);
 for(const size of [{width:1440,height:1000},{width:390,height:844}]){
  await page.setViewportSize(size);
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
 }
 await page.reload();
 await page.locator('#demo-results').filter({hasText:'SIMULATION'}).waitFor();
 assert.match(await page.locator('#demo-message').textContent(),/保存紀錄/);
 const final=await(await fetch(url+'/api/state')).json();
 assert.equal(final.resources.api_calls,initial.resources.api_calls);
 assert.deepEqual(errors,[]);
 console.log('PASS: two ordered simulation stages, empty sessions/prior artifact proof, persisted replay, desktop/mobile, no paid call.');
}finally{await browser.close();}
