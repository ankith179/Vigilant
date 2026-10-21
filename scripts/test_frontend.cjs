/* Browser acceptance against actual persisted records. Never mock research data. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
let playwright;
try { playwright = require('../tools/browser/node_modules/playwright'); }
catch { playwright = require(path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES || '', 'playwright')); }
const root = path.resolve(__dirname, '..');
const origin = process.env.VIGILANT_TEST_URL || 'http://127.0.0.1:8000';
const destination = path.resolve(process.env.VIGILANT_BROWSER_REPORT || path.join(root, 'reports/frontend', new Date().toISOString().replace(/[:.]/g, '-')));
fs.mkdirSync(destination, {recursive:true});
const result = {started_at:new Date().toISOString(), status:'RUNNING', origin,
  platform:process.platform, pages:[], checks:[], errors:[], screenshots:[],
  source_hashes:{}, mutations:process.env.VIGILANT_TEST_MUTATIONS === '1'};
for (const name of ['frontend/src/main.jsx','frontend/src/Graph.jsx','frontend/src/style.css','backend/app.py','database/store.py']) {
  result.source_hashes[name] = require('node:crypto').createHash('sha256').update(fs.readFileSync(path.join(root, name))).digest('hex');
}
let browser;
(async () => {
  browser = await playwright.chromium.launch({headless:true,
    ...(process.env.VIGILANT_BROWSER_EXECUTABLE ? {executablePath:process.env.VIGILANT_BROWSER_EXECUTABLE} : {}),
    args:JSON.parse(process.env.VIGILANT_BROWSER_ARGS || '[]')});
  result.browser = browser.version();
  const context = await browser.newContext({viewport:{width:1440,height:1000}, acceptDownloads:true});
  const page = await context.newPage();
  page.setDefaultTimeout(20000);
  page.on('pageerror', error => result.errors.push(error.message));
  async function get(endpoint) {
    const response = await context.request.get(origin+'/api/'+endpoint);
    assert(response.ok(), endpoint+': '+response.status()); return response.json();
  }
  async function ready() {
    await page.waitForLoadState('networkidle');
    await page.getByText('Loading recorded data…', {exact:true}).waitFor({state:'hidden'});
    await page.getByText('Loading recorded graph…', {exact:true}).waitFor({state:'hidden'});
    await page.locator('main[aria-busy="false"]').waitFor();
  }
  async function visit(name) {
    if (await page.getByRole('heading', {name, exact:true}).isVisible()) { await ready(); return; }
    const endpoints={'Projects':'projects','Repository':'repositories','Artifacts':'artifacts','Traceability':'traceability','Knowledge Graph':'graph','Change Analysis':'changes','Consistency Findings':'findings','Evidence':'evidence','Agent Investigation':'agents','Experiments':'experiments','Reports':'reports'};
    const response = endpoints[name] ? page.waitForResponse(r => new URL(r.url()).pathname === '/api/'+endpoints[name] && r.request().method() === 'GET') : null;
    await page.locator('nav').getByRole('button', {name:new RegExp(name+'$')}).click();
    if(response) await (await response).finished();
    await page.getByRole('heading', {name, exact:true}).waitFor(); await ready();
  }
  async function shot(name) {
    await page.screenshot({path:path.join(destination, name+'.png'), fullPage:true});
    result.screenshots.push(name+'.png');
  }
  const reports = (await get('reports?limit=500')).items;
  const report = reports.find(row => row.config?.model === 'local' && row.changes && row.evidence?.length)
    || reports.find(row => row.changes?.artifacts?.length && row.affected_artifacts?.length);
  assert(report, 'A saved completed investigation is required; no fabricated demo fallback.');
  result.selected_run = report.run_id;
  result.repository = report.repository; result.commit = report.commit_id;
  await page.goto(origin, {waitUntil:'networkidle'});
  await page.getByRole('heading', {name:'Dashboard', exact:true}).waitFor();
  await page.getByLabel('Repository', {exact:true}).selectOption(report.repository);
  await page.getByLabel('Snapshot', {exact:true}).selectOption(report.commit_id);
  await ready();
  const stats = await get('stats');
  assert(stats.artifacts > 0 && stats.graph_edges > 0 && stats.evidence > 0);
  assert.equal(await page.locator('.metric strong').nth(1).innerText(), stats.artifacts.toLocaleString('en-US'));
  await shot('dashboard');
  result.pages.push({page:'Dashboard', stats});
  for (const name of ['Projects','Repository','Artifacts','Traceability','Knowledge Graph','Change Analysis',
    'Impact Analysis','Consistency Findings','Evidence','Agent Investigation','Experiments','Reports']) {
    await visit(name);
    await page.locator('tbody tr').first().waitFor({state:'visible'});
    assert.equal(await page.getByRole('alert').count(), 0, name+' must load without error');
    const rows = await page.locator('tbody tr').count();
    assert(rows > 0, name+' must show persisted records for the selected investigation; scope='+JSON.stringify({repository:await page.getByLabel('Repository',{exact:true}).inputValue(),commit:await page.getByLabel('Snapshot',{exact:true}).inputValue(),body:await page.locator('main').innerText()}));
    result.pages.push({page:name, rows});
  }
  result.checks.push('All 13 pages show persisted data without application errors');
  await visit('Artifacts');
  const first = await page.locator('tbody tr').first().innerText();
  assert.equal(await page.getByRole('button', {name:'Next page', exact:true}).isEnabled(), true);
  const nextPage = page.waitForResponse(r => new URL(r.url()).pathname === '/api/artifacts' && new URL(r.url()).searchParams.get('offset') === '100');
  await page.getByRole('button', {name:'Next page', exact:true}).click();
  await (await nextPage).finished(); await ready();
  await page.waitForFunction(previous => document.querySelector('tbody tr')?.innerText !== previous, first);
  assert.notEqual(await page.locator('tbody tr').first().innerText(), first);
  const previousPage = page.waitForResponse(r => new URL(r.url()).pathname === '/api/artifacts' && new URL(r.url()).searchParams.get('offset') === '0');
  await page.getByRole('button', {name:'Previous page', exact:true}).click();
  await (await previousPage).finished(); await ready();
  await page.waitForFunction(previous => document.querySelector('tbody tr')?.innerText === previous, first);
  assert.equal(await page.locator('tbody tr').first().innerText(), first);
  await page.getByLabel('Filter records').fill('__NO_MATCH_VIGILANT__');
  assert.equal(await page.locator('tbody tr').count(), 0);
  await page.getByLabel('Filter records').fill('');
  await page.locator('tbody tr').first().focus(); await page.keyboard.press('Enter');
  await page.getByRole('heading', {name:'Record & provenance', exact:true}).waitFor();
  assert.equal(JSON.parse(await page.locator('.drawer pre').innerText()).commit_id, report.commit_id);
  await page.getByRole('button', {name:'Close', exact:true}).click();
  result.checks.push('Pagination, local filtering, keyboard record selection and snapshot provenance');
  await visit('Knowledge Graph');
  assert(await page.locator('[data-graph-node]').count() > 0);
  assert(await page.locator('[data-graph-edge][marker-end]').count() > 0);
  const types = await page.getByLabel('Relationship', {exact:true}).locator('option').allTextContents();
  const relationship = types.includes('EXPOSES_API') ? 'EXPOSES_API' : types.find(type => type !== 'All relationships');
  await page.getByLabel('Relationship', {exact:true}).selectOption(relationship);
  assert((await page.locator('tbody tr td:nth-child(2)').allTextContents()).every(text => text === relationship));
  await shot('knowledge-graph');
  await page.locator('[data-graph-node]').first().focus(); await page.keyboard.press('Enter');
  assert(JSON.parse(await page.locator('.drawer pre').innerText()).artifact_id);
  await page.getByRole('button', {name:'Close', exact:true}).click();
  result.checks.push('Directed graph, relationship filter and keyboard-accessible provenance');
  await visit('Evidence');
  await page.locator('tbody tr').first().click();
  const evidence = JSON.parse(await page.locator('.drawer pre').innerText());
  assert(evidence.quote && evidence.content_hash && evidence.start_line >= 1);
  const downloadEvent = page.waitForEvent('download');
  await page.getByRole('button', {name:'Download record ↓', exact:true}).click();
  const download = await downloadEvent;
  await download.saveAs(path.join(destination, 'downloaded-evidence.json'));
  assert.deepEqual(JSON.parse(fs.readFileSync(path.join(destination, 'downloaded-evidence.json'))), evidence);
  await shot('evidence'); await page.getByRole('button', {name:'Close', exact:true}).click();
  result.checks.push('Evidence quote/hash/range and exact JSON export');
  await visit('Reports');
  await page.locator('tbody tr').first().click();
  const fullReport = JSON.parse(await page.locator('.drawer pre').innerText());
  assert(fullReport.changes, 'Saved report must expose report exports');
  for (const format of ['json','csv','html']) {
    const pending = page.waitForEvent('download');
    await page.getByRole('button', {name:'Export '+format.toUpperCase(), exact:true}).click();
    const exported = await pending;
    const file = path.join(destination, 'report-export.'+format);
    await exported.saveAs(file);
    assert(fs.statSync(file).size > 0);
    if (format === 'json') assert.equal(JSON.parse(fs.readFileSync(file)).run_id, fullReport.run_id);
  }
  await page.getByRole('button', {name:'Close', exact:true}).click();
  await visit('Dashboard');
  const providers = await page.getByLabel('Reasoning provider').locator('option').evaluateAll(options => options.map(x=>x.value));
  assert(providers.includes('omniroute') && !providers.includes('cloud'));
  await page.getByLabel('Reasoning provider').selectOption('ollama');
  assert.deepEqual(await page.getByLabel('Local model', {exact:true}).locator('option').evaluateAll(xs=>xs.map(x=>x.value)), ['qwen3:8b','qwen2.5-coder:14b','qwen3:14b']);
  await page.getByLabel('Local model', {exact:true}).selectOption('qwen3:14b');
  await page.getByLabel('Reasoning provider').selectOption('none');
  result.checks.push('Three local model choices and provider switching');
  await page.locator('summary').filter({hasText:'Workspace access'}).click();
  assert(await page.getByLabel('Workspace access token').isVisible());
  await page.locator('summary').filter({hasText:'Workspace access'}).click();
  result.checks.push('JSON/CSV/HTML report downloads, free OmniRoute selector and access settings');
  // An explicit injected transport failure exercises UI recovery only, never accuracy.
  await page.route('**/api/traceability?*', route => route.fulfill({status:503, contentType:'application/json', body:'{"detail":"Validation transport failure"}'}));
  await visit('Traceability');
  assert.match(await page.getByRole('alert').innerText(), /Validation transport failure/);
  await page.unroute('**/api/traceability?*');
  const refreshed = page.waitForResponse(r => new URL(r.url()).pathname === '/api/traceability' && r.ok());
  await page.getByRole('button', {name:'↻ Refresh', exact:true}).click();
  await (await refreshed).finished(); await ready();
  await page.getByRole('alert').waitFor({state:'hidden'});
  assert.equal(await page.getByRole('alert').count(), 0);
  result.checks.push('Transport error shown and real API refresh recovers');
  if (result.mutations) {
    // Enable only on an isolated copy of the database. No LLM or external API call.
    await visit('Projects');
    const name = 'Browser validation '+result.started_at;
    await page.getByLabel('Project name').fill(name);
    await page.getByRole('button', {name:'Create project', exact:true}).click(); await ready();
    assert((await get('projects?limit=500')).items.some(row => row.name === name));
    await visit('Dashboard');
    await page.getByLabel('Base revision').fill(report.base_commit);
    await page.getByLabel('Reasoning provider').selectOption('none');
    const posted = page.waitForResponse(response => response.url().endsWith('/api/analysis/run') && response.request().method() === 'POST');
    await page.getByRole('button', {name:'Investigate change →', exact:true}).click();
    const job = await (await posted).json();
    await page.getByRole('heading', {name:'Reports', exact:true}).waitFor({timeout:180000}); await ready();
    const completed = await get('reports/'+job.job_id); assert.equal(completed.status, 'COMPLETED');
    const actual = await get('reports/'+completed.result_run_id);
    assert(actual.trajectory.every(stage => stage.status === 'SUCCESS'));
    assert(actual.evidence.length > 0 && actual.config.model === 'none');
    fs.writeFileSync(path.join(destination, 'ui-investigation.json'), JSON.stringify(actual, null, 2));
    result.checks.push('Project creation and complete deterministic investigation through UI on isolated database');
  }
  await visit('Reports'); await page.locator('tbody tr').first().click(); await shot('report-detail');
  await page.getByRole('button', {name:'Close', exact:true}).click();
  await page.setViewportSize({width:390,height:844});
  await visit('Dashboard'); await shot('mobile-dashboard');
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1), 'No mobile document overflow');
  await visit('Knowledge Graph'); await shot('mobile-graph');
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1));
  result.checks.push('390px mobile dashboard and graph without document overflow');
  assert.deepEqual(result.errors, []);
  result.status = 'PASSED';
})().catch(error => {result.status='FAILED'; result.failure=error.stack; process.exitCode=1; console.error(error);})
  .finally(async () => {
    if (browser) await browser.close();
    result.finished_at=new Date().toISOString();
    fs.writeFileSync(path.join(destination, 'validation.json'), JSON.stringify(result, null, 2)+'\n');
    console.log(JSON.stringify({status:result.status, report:path.join(destination, 'validation.json')}));
  });
