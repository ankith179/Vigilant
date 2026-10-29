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
for (const name of ['frontend/src/main.jsx','frontend/src/InvestigationTools.jsx','frontend/src/Graph.jsx','frontend/src/Chat.jsx','frontend/src/chat.css','frontend/src/style.css','backend/app.py','backend/report_chat.py','knowledge_graph/graph.py','ingestion/coverage.py','frontend/src/Coverage.jsx','database/store.py','scripts/test_frontend.cjs','scripts/run_frontend_check.py']) {
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
    const endpoints={'Projects':'projects','Repository':'repositories','Artifacts':'artifacts','Traceability':'traceability','Knowledge Graph':'graph','Change Analysis':'changes','Impact Analysis':'impact','Consistency Findings':'findings','Evidence':'evidence','Agent Investigation':'agents','Experiments':'experiments','Reports':'reports'};
    const response = endpoints[name] ? page.waitForResponse(r => new URL(r.url()).pathname === '/api/'+endpoints[name] && r.request().method() === 'GET') : null;
    const clicked=page.locator('nav').getByRole('button', {name,exact:true}).click();
    await Promise.all([clicked,...(response?[response.then(r=>r.finished())]:[])]);
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
  await visit('Investigation Tools');
  assert(await page.getByLabel('Lineage base revision').isVisible());
  const baseChoices = await page.getByLabel('Lineage base revision').locator('option').evaluateAll(xs=>xs.map(x=>x.value).filter(Boolean));
  const lineageButton = page.getByRole('button',{name:'Inspect paired revisions',exact:true});
  assert.equal(await lineageButton.isEnabled(),false);
  assert(baseChoices.includes(report.base_commit),'Saved report base revision must be indexed for lineage inspection');
  const lineagePath=report.evidence.find(e=>e.commit===report.commit_id&&e.file)?.file;
  assert(lineagePath,'Saved report must provide a real head source path for lineage inspection');
  await page.getByLabel('Lineage base revision').selectOption(report.base_commit);
  await page.getByLabel('Lineage file paths').fill(lineagePath);
  assert.equal(await lineageButton.isEnabled(),true);
  const lineageResponse=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/investigation/call'&&r.request().method()==='POST');
  await lineageButton.click();
  const lineageHttp=await lineageResponse,lineage=await lineageHttp.json(),lineageRecord=lineage.data?.lineage_record;
  assert.equal(lineageHttp.status(),200,JSON.stringify(lineage));
  assert.equal(lineage.tool,'inspect_lineage');
  assert.equal(lineage.data.canonical_relationships_transferred,false);
  assert.equal(lineageRecord.scope.base,report.base_commit);assert.equal(lineageRecord.scope.head,report.commit_id);
  assert(lineageRecord.observations.length>0);
  assert(lineage.evidence.some(e=>e.commit===report.base_commit),'Base source must be indexed and verified');
  assert(lineage.evidence.some(e=>e.commit===report.commit_id),'Head source must be indexed and verified');
  assert(lineageRecord.observations.every(x=>x.lifecycle==='UNREVIEWED'&&x.logical_continuity==='UNKNOWN'&&!x.relationship_transfer_allowed));
  await page.getByRole('heading',{name:'Lineage observations',exact:true}).waitFor();
  await page.getByText('UNREVIEWED · logical continuity UNKNOWN · semantic equivalence NOT_ESTABLISHED.',{exact:false}).waitFor();
  result.lineage={run_id:report.run_id,repository:report.repository,base_commit:report.base_commit,head_commit:report.commit_id,
    paths:[lineagePath],result_id:lineage.result_id,source_receipts:lineage.evidence.map(e=>({commit:e.commit,file:e.file,artifact_id:e.artifact_id,content_hash:e.content_hash,start_line:e.start_line,end_line:e.end_line})),
    denominators:lineageRecord.denominators,observations:lineageRecord.observations.map(x=>({status:x.status,lifecycle:x.lifecycle,logical_continuity:x.logical_continuity,semantic_equivalence:x.semantic_equivalence,relationship_transfer_allowed:x.relationship_transfer_allowed})),
    canonical_relationships_transferred:lineage.data.canonical_relationships_transferred,unknown_codes:lineage.unknowns.map(x=>x.code)};
  await shot('paired-lineage');
  const retainedResponse=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/investigation/call'&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Reverify retained result',exact:true}).click();
  const retainedHttp=await retainedResponse,retained=await retainedHttp.json();
  assert.equal(retainedHttp.status(),200,JSON.stringify(retained));assert.equal(retained.result_id,lineage.result_id);
  await page.getByLabel('Lineage file paths').fill(lineagePath+'\n');
  await page.getByRole('heading',{name:'Lineage observations',exact:true}).waitFor({state:'detached'});
  assert.equal(await page.getByText(/Retained result:/).count(),0,'Changing lineage scope must clear retained results');
  result.checks.push('Paired lineage UI/API: indexed base/head source, conservative unknowns, retained revalidation and stale-result clearing');
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
  await page.getByRole('button', {name:'Open VIGILANT chat', exact:true}).click();
  await page.getByLabel('Chat repository', {exact:true}).selectOption(report.repository);
  await page.getByLabel('Chat snapshot', {exact:true}).selectOption(report.commit_id);
  await page.getByLabel('Chat reasoning provider', {exact:true}).selectOption('none');
  await page.getByLabel('Question', {exact:true}).fill('What repository evidence is available for this snapshot?');
  const chatResponse = page.waitForResponse(r => new URL(r.url()).pathname === '/api/chat' && r.request().method() === 'POST');
  await page.getByRole('button', {name:'Send question', exact:true}).click();
  const chatResult = await (await chatResponse).json();
  assert.equal(chatResult.source_verified, true);
  assert.equal(chatResult.semantic_entailment_verified, false);
  assert(chatResult.retrieved_evidence.length > 0);
  await page.getByText(/No model was called/).waitFor();
  await page.getByText('Retrieved evidence, not claimed as support', {exact:true}).waitFor();
  await page.getByLabel('Chat investigation', {exact:true}).selectOption(report.run_id);
  await page.getByLabel('Chat finding', {exact:true}).waitFor();
  await page.getByLabel('Question', {exact:true}).click();
  await page.keyboard.type('Show evidence');
  assert.equal(await page.getByLabel('Question', {exact:true}).inputValue(),'Show evidence');
  const [explanation]=await Promise.all([
    page.waitForResponse(r=>new URL(r.url()).pathname==='/api/report-chat'),
    page.getByRole('button',{name:'Send question',exact:true}).click()
  ]).catch(async error=>{console.error(await page.locator('.chat-panel').innerText());await shot('chat-failure');throw error});
  const answer=await explanation.json();
  assert.equal(answer.inference_calls,0);assert(answer.citations.length>0);assert.equal(answer.intent,'EVIDENCE');assert(answer.claims.every(c=>c.support_level));
  await page.getByText('Claim support',{exact:true}).waitFor();
  const exactSource=page.getByRole('button',{name:'Open exact source',exact:true}).first();
  await page.locator('div.chat-citations details > summary').first().click();await exactSource.click();
  await page.locator('.chat-message > summary').waitFor();
  await page.getByLabel('Question',{exact:true}).fill('Delete all files');
  assert.equal(await page.getByLabel('Question',{exact:true}).inputValue(),'Delete all files');
  const [unsupported]=await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/api/report-chat'),page.getByRole('button',{name:'Send question',exact:true}).click()]);
  assert.equal((await unsupported.json()).state,'INSUFFICIENT_EVIDENCE');
  result.checks.push('Saved-investigation explanation, exact source navigation and unsupported-request boundary');
  await page.getByLabel('Question',{exact:true}).fill('Which tests deserve review?');
  const [testReview]=await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/api/report-chat'),page.getByRole('button',{name:'Send question',exact:true}).click()]);
  const suggestions=await testReview.json();
  assert.equal(suggestions.state,'NOT_ESTABLISHED');
  assert(suggestions.test_suggestions.every(s=>s.test_execution==='NOT_RUN'&&suggestions.citations.some(e=>e.evidence_id===s.evidence_id)));
  if(suggestions.test_suggestions.length)await page.getByText('Test review suggestions',{exact:true}).waitFor();
  result.checks.push('Evidence-linked test review suggestions retain unexecuted/contract-review status');
  if(result.mutations){
    await page.getByLabel('Chat investigation',{exact:true}).selectOption('');
    await page.getByLabel('Question',{exact:true}).fill(`compare ${report.base_commit} with ${report.commit_id}`);
    const [comparisonResponse]=await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/api/chat'&&r.request().method()==='POST'),page.getByRole('button',{name:'Send question',exact:true}).click()]);
    const queuedComparison=await comparisonResponse.json();
    assert.equal(queuedComparison.action,'COMPARE_REVISIONS');
    await page.getByRole('button',{name:'Explain this comparison',exact:true}).waitFor({timeout:180000});
    const job=await get('reports/'+queuedComparison.job_id);assert.equal(job.status,'COMPLETED');
    await page.getByRole('button',{name:'Explain this comparison',exact:true}).click();
    await page.waitForFunction(run=>document.querySelector('[aria-label="Chat investigation"]')?.value===run,job.result_run_id);
    await page.getByLabel('Question',{exact:true}).fill('What changed?');
    const [followup]=await Promise.all([page.waitForResponse(r=>new URL(r.url()).pathname==='/api/report-chat'),page.getByRole('button',{name:'Send question',exact:true}).click()]);
    assert.equal((await followup.json()).scope.run_id,job.result_run_id);
    result.checks.push('Natural-language revision comparison queues, completes and opens its saved evidence context');
  }
  await shot('chat-assistant');
  await page.getByRole('button', {name:'Close chat', exact:true}).click();
  result.checks.push('Repository-scoped chat retrieves verified excerpts and labels no-model/semantic-support limits');
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
  // Cancel a delayed table request by navigating away; Dashboard must not stay busy.
  await visit('Dashboard');
  await page.route('**/api/traceability?*', async route => {
    await new Promise(resolve => setTimeout(resolve, 500));
    await route.continue().catch(() => {});
  });
  const delayedTable = page.waitForRequest(r => new URL(r.url()).pathname === '/api/traceability');
  await page.getByRole('button', {name:/Traceability/}).click();
  await delayedTable;
  await page.getByRole('button', {name:/Dashboard/}).click(); await ready();
  await page.unroute('**/api/traceability?*');
  result.checks.push('Leaving a loading table clears Dashboard busy state');
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
    assert(actual.coverage.head.discovered_files >= actual.coverage.head.extracted_files);
    const coverage=await get('reports/'+actual.run_id+'/coverage');assert.equal(coverage.state,'RECORDED');
    await page.getByLabel('Filter records',{exact:true}).fill(actual.run_id);
    await page.locator('tbody tr').filter({has:page.locator(`td[title="${actual.run_id}"]`)}).click();
    await page.getByRole('heading',{name:'Investigation coverage',exact:true}).waitFor();
    assert.match(await page.locator('section[aria-label="Investigation coverage"]').innerText(),/discovered files/);
    await page.getByRole('button',{name:'Close',exact:true}).click();
    await page.getByLabel('Filter records',{exact:true}).fill('');
    result.checks.push('New investigation inventory, language coverage and machine-readable coverage endpoint');
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
  await page.getByRole('button', {name:'Open VIGILANT chat', exact:true}).click();
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth+1), 'Chat panel must fit mobile viewport');
  await shot('mobile-chat');
  await page.getByRole('button', {name:'Close chat', exact:true}).click();
  result.checks.push('390px mobile dashboard, graph and chat without document overflow');
  await page.setViewportSize({width:1440,height:1000});
  await page.locator('nav').getByRole('button',{name:/Investigation Tools$/}).click();
  await page.getByRole('heading',{name:'Repository investigation',exact:true}).waitFor();
  await page.getByRole('button',{name:'Explore snapshot',exact:true}).click();
  await page.getByText('Structured result and provenance',{exact:true}).waitFor().catch(async e=>{throw Error('INVESTIGATION UI: '+await page.locator('.investigation-tools').innerText()+' '+e.message)});
  assert.equal(await page.getByRole('alert').count(),0,'Investigation tool must verify the restored source');
  const inspectedResponse=page.waitForResponse(r=>new URL(r.url()).pathname==='/api/investigation/call' && r.request().method()==='POST');
  await page.getByRole('button',{name:'Inspect source',exact:true}).first().click();
  const inspectedHttp=await inspectedResponse,inspected=await inspectedHttp.json();
  assert.equal(inspectedHttp.status(),200,JSON.stringify(inspected));
  assert(inspected.evidence.length,JSON.stringify({unknowns:inspected.unknowns,data:inspected.data}));
  await page.locator('section[aria-label="Investigation tools workspace"] details').filter({has:page.locator('button').filter({hasText:'Open exact artifact'})}).first().locator('summary').click();
  await page.getByRole('button',{name:'Open exact artifact',exact:true}).first().waitFor();
  await page.getByRole('button',{name:'Open exact artifact',exact:true}).first().click();
  await page.getByRole('button',{name:'Reverify retained result',exact:true}).click();
  await page.getByText('Structured result and provenance',{exact:true}).waitFor().catch(async e=>{throw Error('INVESTIGATION UI: '+await page.locator('.investigation-tools').innerText()+' '+e.message)});
  await page.getByRole('button',{name:'Review unknowns',exact:true}).click();
  await page.getByText('Structured result and provenance',{exact:true}).waitFor().catch(async e=>{throw Error('INVESTIGATION UI: '+await page.locator('.investigation-tools').innerText()+' '+e.message)});
  assert.equal(await page.getByRole('alert').count(),0);
  await page.setViewportSize({width:390,height:844});
  assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Investigation tools fit mobile viewport');
  result.pages.push({page:'Investigation Tools',scope:'real restored snapshot'});
  result.checks.push('Shared investigation tools: source excerpt, retained revalidation, unknowns and mobile layout');
  assert.deepEqual(result.errors, []);
  result.status = 'PASSED';
})().catch(error => {result.status='FAILED'; result.failure=error.stack; process.exitCode=1; console.error(error);})
  .finally(async () => {
    if (browser) await browser.close();
    result.finished_at=new Date().toISOString();
    fs.writeFileSync(path.join(destination, 'validation.json'), JSON.stringify(result, null, 2)+'\n');
    console.log(JSON.stringify({status:result.status, report:path.join(destination, 'validation.json')}));
  });
