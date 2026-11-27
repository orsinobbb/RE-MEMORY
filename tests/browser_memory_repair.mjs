import {loadPlaywright,browserLaunchOptions} from '../scripts/playwright_runtime.mjs';
import assert from 'node:assert/strict';
const playwright=loadPlaywright();
const baseURL = process.env.REMEMORY_BASE_URL || 'http://127.0.0.1:8792';
const original = await (await fetch(`${baseURL}/api/state`)).json();
assert.equal(original.settings.enabled, false, 'Only run against the disposable live-disabled fixture.');
assert.equal(original.resources.api_calls, 0);
const browser = await playwright.chromium.launch(browserLaunchOptions());
const page = await browser.newPage({viewport:{width:1440,height:1000}});
page.setDefaultTimeout(10000);
const errors=[]; page.on('pageerror',error=>errors.push(error.message));
async function response(path, click) {
  const pending=page.waitForResponse(r=>r.url().endsWith(path)&&r.request().method()==='POST');
  await click(); return await pending;
}
try {
  await page.goto(baseURL);
  await page.locator('[data-testid="backend-status"]').filter({hasText:'CONNECTED'}).waitFor();
  await page.locator('#query').fill('我要你繼續做昨天的音樂專案。');
  await page.locator('[data-testid="run-retrieval"]').click();
  await page.locator('#retrieval-status').filter({hasText:'RESOLVED'}).waitFor();
  await page.locator('[data-view="memory"]').click();
  await page.locator('#memory-project').selectOption('PROJECT-028');
  await page.locator('[data-testid="memory-fact"]').filter({hasText:'PROJECT-028-goal-v2'}).waitFor();
  const aliasButton=page.locator('[data-testid="confirm-alias"]').first();
  await aliasButton.waitFor();
  const aliasResponse=await response('/confirm',()=>aliasButton.click());
  assert.equal(aliasResponse.status(),200);
  await page.locator('#global-message').filter({hasText:'稱呼已確認'}).waitFor();
  assert.equal(await page.locator('#retrieval-status').textContent(),'STALE');
  const goal=page.locator('[data-testid="memory-fact"]').filter({hasText:'PROJECT-028-goal-v2'});
  await goal.locator('[data-testid="revise-fact"]').click();
  const form=goal.locator('[data-testid="fact-revision-form"]');
  await form.locator('textarea').fill('這段內容並未出現在來源');
  const unsupported=await response('/revise',()=>form.locator('button[type="submit"]').click());
  assert.equal(unsupported.status(),409);
  await form.locator('[role="alert"]').filter({hasText:'SOURCE_SUPPORTED'}).waitFor();
  await form.locator('textarea').fill('MIDI 轉換驗收清單');
  const supported=await response('/revise',()=>form.locator('button[type="submit"]').click());
  assert.equal(supported.status(),200);
  const updated=await supported.json();
  assert.equal(updated.version,3); assert.equal(updated.verification,'VERIFIED');
  await page.locator('[data-testid="memory-fact"]').filter({hasText:updated.id}).waitFor();
  const old=page.locator('[data-testid="memory-fact"]').filter({hasText:'PROJECT-028-goal-v2'});
  assert.match(await old.textContent(),/SUPERSEDED/);
  assert.equal(await old.locator('[data-testid="revise-fact"]').count(),0);
  const artifact=page.locator('[data-artifact-id="prior-PROJECT-028"]');
  await artifact.locator('[data-testid="review-artifact"]').click();
  const review=artifact.locator('[data-testid="artifact-review-form"]');
  await review.waitFor();
  assert.equal(await review.locator('button[type="submit"]').isDisabled(),true);
  await review.locator('input[type="checkbox"]').check();
  const saved=await response('/revalidate',()=>review.locator('button[type="submit"]').click());
  assert.equal(saved.status(),200); const revision=await saved.json();
  assert.equal(revision.factual_status,'CLAIM');
  await page.locator(`[data-artifact-id="${revision.id}"]`).waitFor();
  assert.equal(await page.locator('[data-artifact-id="prior-PROJECT-028"]').locator('[data-testid="review-artifact"]').count(),0);
  for (const size of [{width:1440,height:1000},{width:390,height:844}]) {
    await page.setViewportSize(size);
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    // A second source-backed revision exercises the inline form at both sizes.
    const current=page.locator('[data-testid="memory-fact"]').filter({hasText:updated.id});
    await current.locator('[data-testid="revise-fact"]').click();
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1));
    await current.locator('[data-testid="fact-revision-form"] button[type="button"]').click();
  }
  const final=await (await fetch(`${baseURL}/api/state`)).json();
  assert.equal(final.resources.api_calls,0); assert.equal(final.resources.known_api_tokens,0);
  const memory=await (await fetch(`${baseURL}/api/memory?project_id=PROJECT-028`)).json();
  assert.equal(memory.tasks.find(t=>t.id==='done-PROJECT-028').status,'COMPLETED');
  assert.equal(memory.tasks.find(t=>t.id==='done-PROJECT-028').artifact_id,revision.id);
  assert.deepEqual(errors,[]);
  console.log('PASS: alias confirmation, rejected unsupported edit, immutable fact revision, acknowledged artifact revision, stale context cleared, desktop/mobile, zero paid calls.');
} finally { await browser.close(); }
