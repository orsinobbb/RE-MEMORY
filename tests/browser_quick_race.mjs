import assert from 'node:assert/strict';
import {loadPlaywright,browserLaunchOptions} from '../scripts/playwright_runtime.mjs';
const browser=await loadPlaywright().chromium.launch(browserLaunchOptions());
const page=await browser.newPage();page.setDefaultTimeout(6000);
let release;let entered;const waiting=new Promise(r=>entered=r);const gate=new Promise(r=>release=r);let executions=0;
try{
 await page.route('**/api/session',async route=>{entered();await gate;await route.fulfill({json:{id:'unpaid-test-session',raw_history_count:0}});});
 await page.route('**/api/execute',async route=>{executions++;await route.fulfill({json:{status:'BLOCKED',reason:'UNPAID_UI_TEST',mode:'SIMULATION'}});});
 await page.goto('http://127.0.0.1:8791/#workspace');
 await page.locator('[data-testid="backend-status"]').filter({hasText:'CONNECTED'}).waitFor();
 await page.locator('#query').fill('請接續AI 工作管理，完成目前尚未完成的驗收清單。');
 await page.locator('[data-testid="run-retrieval"]').click();
 await page.locator('#quick-context').filter({hasText:'找到專案：AI 工作管理'}).waitFor();
 await page.locator('#execution-mode').selectOption('SIMULATION');
 await page.locator('[data-testid="execute-task"]').click();await waiting;
 assert.equal(await page.getByRole('button',{name:'填入鋼琴教材範例'}).isDisabled(),true,'Example cannot replace the confirmed query during pending Session.');
 assert.equal(await page.locator('#execution-mode').isDisabled(),true,'Mode cannot become paid while Session is pending.');
 assert.equal(await page.locator('#execution-model').isDisabled(),true);
 await page.locator('#query').evaluate(n=>{n.value='請接續鋼琴樂理教材，完成目前尚未完成的驗收清單。';});
 release();await page.locator('[data-testid="execute-task"]').filter({hasText:'確認'}).waitFor();
 assert.equal(executions,0,'Changed confirmation must stop before generation.');
 console.log('PASS: frozen query/example/mode/model and post-session revalidation; zero provider calls.');
}finally{release?.();await browser.close();}
