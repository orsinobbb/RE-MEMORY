import {loadPlaywright,browserLaunchOptions} from '../scripts/playwright_runtime.mjs';
import assert from 'node:assert/strict';

// Real same-origin integration smoke test. No paid execution and no mock scores.
// Start the application separately, then run this file with the bundled Node.
const playwright=loadPlaywright();
const baseURL = process.env.REMEMORY_BASE_URL || 'http://127.0.0.1:8791';
let health;
try {
  health = await fetch(`${baseURL}/api/health`);
} catch {
  assert.fail(`Backend is not running at ${baseURL}; start it before browser integration smoke.`);
}
assert.equal(health.status, 200, 'backend health must be reachable');
assert.equal((await health.json()).status, 'ok', 'The port is reachable but the RE:MEMORY backend is not running here.');

const browser = await playwright.chromium.launch(browserLaunchOptions());
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
const errors = [];
page.on('pageerror', error => errors.push(error.message));

async function navigate(view) {
  await page.locator(`[data-view="${view}"]`).click();
  await page.locator(`#view-${view}`).waitFor({ state: 'visible' });
  assert.equal(await page.locator(`[data-view="${view}"]`).getAttribute('aria-current'), 'page');
}

async function noPageOverflow(label) {
  const dimensions = await page.evaluate(() => ({
    document: document.documentElement.scrollWidth,
    viewport: window.innerWidth,
  }));
  assert.ok(dimensions.document <= dimensions.viewport + 1, `${label}: page must not overflow horizontally (${JSON.stringify(dimensions)})`);
}

try {
  await page.goto(baseURL);
  await page.locator('[data-testid="backend-status"]').filter({ hasText: 'CONNECTED' }).waitFor();
  assert.equal(await page.locator('[data-testid="dataset-label"]').textContent(), 'DEMO DATASET');
  assert.ok(await page.locator('[data-testid="project-card"]').count() > 0, 'workspace projects come from backend');
  await page.locator('#query').fill('我要你繼續做昨天的音樂專案。');
  await page.locator('#budget').selectOption('4096');
  await page.locator('[data-testid="run-retrieval"]').click();
  await page.locator('[data-testid="retrieval-status"]').filter({ hasText: /RESOLVED|NEEDS_CONFIRMATION|NOT_FOUND|BUDGET_EXCEEDED/ }).waitFor({ state: 'attached', timeout: 30000 });
  assert.ok(await page.locator('[data-testid="retrieval-round"]').count() > 0, 'query has real retrieval rounds');
  assert.match(await page.locator('[data-testid="trace-source"]').textContent(), /LIVE SSE|SAVED REPLAY/);
  await noPageOverflow('desktop observatory');

  await navigate('context');
  assert.ok((await page.locator('[data-testid="context-result"]').textContent()).includes('Memory manifest'));
  assert.ok(await page.locator('[data-testid="token-category"]').count() >= 8, 'context displays all budget categories');

  await navigate('memory');
  await page.locator('[data-testid="memory-fact"]').first().waitFor();
  await page.locator('#memory-search').fill('音樂');
  await page.locator('#memory-search-form').evaluate(form => form.requestSubmit());
  await page.locator('[data-testid="memory-load-state"]').filter({ hasText: 'Loaded' }).waitFor();

  await navigate('recovery');
  const sessionResponse = page.waitForResponse(response => response.url().endsWith('/api/session') && response.request().method() === 'POST');
  await page.locator('[data-testid="new-session"]').click();
  const session = await (await sessionResponse).json();
  assert.equal(session.raw_history_count, 0, 'fresh session must have no raw history');
  await page.locator('[data-testid="session-history"]').filter({ hasText: '0' }).waitFor();
  await navigate('workspace');
  await page.locator('#execution-mode').selectOption('SIMULATION');
  const executeResponse = page.waitForResponse(response => response.url().endsWith('/api/execute') && response.request().method() === 'POST');
  await page.locator('[data-testid="execute-task"]').click();
  const execution = await (await executeResponse).json();
  assert.ok(['COMPLETED', 'ALREADY_COMPLETED'].includes(execution.status), `simulation must produce or recover an artifact: ${execution.reason || execution.status}`);
  assert.equal(execution.mode, 'SIMULATION');
  assert.ok(execution.artifact?.content, 'simulation response must contain a real persisted artifact');
  await page.waitForFunction(content => document.querySelector('[data-testid="artifact-content"]').textContent === content, execution.artifact.content);
  assert.equal(await page.locator('[data-testid="artifact-content"]').textContent(), execution.artifact.content);
  assert.ok((await page.locator('[data-testid="artifact-download"]').getAttribute('href')).includes(encodeURIComponent(execution.artifact.id)));

  await navigate('benchmark');
  await page.locator('#benchmark-count').selectOption('10');
  for (const checkbox of await page.locator('input[name="benchmark-budget"]').all()) await checkbox.uncheck();
  await page.locator('input[name="benchmark-budget"][value="4096"]').check();
  const benchmarkResponse = page.waitForResponse(response => response.url().endsWith('/api/benchmark') && response.request().method() === 'POST');
  await page.locator('[data-testid="run-benchmark"]').click();
  const benchmark = await (await benchmarkResponse).json();
  assert.equal(benchmark.mode, 'OFFLINE_RETRIEVAL');
  assert.ok(benchmark.results.length > 0, 'benchmark returned actual measured rows');
  await page.locator('[data-testid="benchmark-row"]').first().waitFor();
  assert.equal(await page.locator('[data-testid="benchmark-row"]').count(), benchmark.results.length);
  assert.ok(await page.locator('[data-testid="benchmark-results"]').textContent().then(text => text.includes('UNKNOWN')), 'null live metrics remain UNKNOWN');
  assert.ok((await page.locator('[data-testid="benchmark-export"]').getAttribute('href')).endsWith(encodeURIComponent(benchmark.id)));

  for (const viewport of [{ width: 1440, height: 1000 }, { width: 390, height: 844 }]) {
    await page.setViewportSize(viewport);
    for (const view of ['workspace', 'memory', 'observatory', 'context', 'recovery', 'benchmark']) {
      await navigate(view);
      await noPageOverflow(`${viewport.width}px ${view}`);
    }
  }
  assert.deepEqual(errors, [], 'frontend must not throw uncaught errors');
  console.log('PASS: six views, real retrieval/context, fresh-session simulation artifact, offline benchmark, desktop/mobile overflow.');
} finally {
  await browser.close();
}
