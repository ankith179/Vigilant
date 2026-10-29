/* Real saved development reports through production UI; no labels or model calls. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const root=path.resolve(__dirname,'..'),origin=process.env.VIGILANT_TEST_URL;
const pw=process.env.VIGILANT_BROWSER_MODULE||path.join(process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES||'','playwright');
const {chromium}=require(pw),destination=process.env.VIGILANT_BROWSER_REPORT;
if(!origin||!destination)throw Error('Explicit isolated test URL and output directory required');
fs.mkdirSync(destination,{recursive:true});
const saved=JSON.parse(fs.readFileSync(path.join(root,'reports/staged-report-20261025/reports/result.json')));
const result={status:'RUNNING',started_at:new Date().toISOString(),platform:process.platform,playwright:require(pw+'/package.json').version,
  cases:saved.cases,rows:[],checks:[],errors:[],model_calls:0,independent_labels_created:0,quality_target:'NOT_EVALUATED',source_hashes:{}};
for(const file of ['frontend/src/PartialReports.jsx','frontend/src/main.jsx','backend/partial_reports.py','backend/partial_delivery.py','backend/app.py','scripts/test_partial_reports.cjs'])result.source_hashes[file]=crypto.createHash('sha256').update(fs.readFileSync(path.join(root,file))).digest('hex');
let browser;
(async()=>{
  browser=await chromium.launch({headless:true,...(process.env.VIGILANT_BROWSER_EXECUTABLE?{executablePath:process.env.VIGILANT_BROWSER_EXECUTABLE}:{})});
  result.browser=browser.version();
  const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
  if(process.env.VIGILANT_ACCESS_TOKEN)await context.addInitScript(token=>sessionStorage.setItem('vigilant-token',token),process.env.VIGILANT_ACCESS_TOKEN);
  const page=await context.newPage();page.setDefaultTimeout(30000);page.on('pageerror',e=>result.errors.push(e.message));
  await page.goto(origin,{waitUntil:'networkidle'});
  await page.locator('nav').getByRole('button',{name:/Partial Reports$/}).click();
  await page.getByRole('heading',{name:'Partial development reports',exact:true}).waitFor();
  await page.getByText('Loading partial report catalog…',{exact:true}).waitFor({state:'hidden'});
  if(process.env.VIGILANT_PARTIAL_REPORT_MANIFEST_SHA256){
    for(let offset=0;offset<saved.cases;offset+=10){
      for(const row of saved.rows.slice(offset,offset+10)){
        if(row.status!=='COMPOSED'){result.rows.push({case_id:row.case_id,status:'UNAVAILABLE_RETAINED'});continue;}
        const expected=JSON.parse(fs.readFileSync(path.join(root,'reports/staged-report-20261025/reports',row.path)));
        await page.getByRole('button',{name:'Open partial report '+row.case_id,exact:true}).click();
        await page.getByRole('heading',{name:'Review: '+row.case_id,exact:true}).waitFor();
        const article=page.getByRole('article',{name:'Selected partial report'});
        await article.getByText(expected.report_id,{exact:true}).waitFor();
        assert((await article.innerText()).includes(expected.scope.base_commit));
        assert((await article.innerText()).includes(expected.scope.head_commit));
        assert((await article.innerText()).includes((expected.observed_outcomes.artifacts.UNKNOWN||0)+' UNKNOWN artifact outcomes'));
        assert.equal(await page.getByRole('alert').count(),0);
        result.rows.push({case_id:row.case_id,status:'UI_REPORT_VERIFIED',report_id:expected.report_id,unknowns:expected.unknown_artifact_observations.length});
      }
      if(offset+10<saved.cases){
        await page.getByRole('button',{name:'Next reports',exact:true}).click();
        await page.getByRole('button',{name:'Open partial report '+saved.rows[offset+10].case_id,exact:true}).waitFor();
      }
    }
    while(!(await page.getByRole('button',{name:'Previous reports',exact:true}).isDisabled())){
      await page.getByRole('button',{name:'Previous reports',exact:true}).click();
      await page.getByText('Loading partial report catalog…',{exact:true}).waitFor({state:'hidden'});
    }
    const first=saved.rows[0],expected=JSON.parse(fs.readFileSync(path.join(root,'reports/staged-report-20261025/reports',first.path)));
    const open=page.getByRole('button',{name:'Open partial report '+first.case_id,exact:true});
    await open.click();await page.getByRole('heading',{name:'Review: '+first.case_id,exact:true}).waitFor();
    await open.click();await page.getByRole('heading',{name:'Review: '+first.case_id,exact:true}).waitFor();
    result.checks.push('Repeated selection revalidates rather than leaving an empty report');
    await page.getByRole('button',{name:'Inspect source 1',exact:true}).click();
    const excerpt=page.getByLabel('Verified source excerpt',{exact:true});await excerpt.waitFor();
    assert((await excerpt.innerText()).includes(expected.evidence[0].quote.split('\n')[0]));
    await page.getByLabel('Source start line',{exact:true}).fill('2');
    await page.getByRole('button',{name:'Inspect lines',exact:true}).click();
    await excerpt.waitFor();assert((await excerpt.innerText()).startsWith('2:'));
    await page.getByRole('button',{name:'Close source',exact:true}).click();
    result.checks.push('Exact selected revision source and bounded line navigation');
    await page.locator('.partial-graph').first().locator('summary').first().click();
    await page.getByRole('table',{name:'base graph candidates',exact:true}).getByRole('button').first().click();
    await excerpt.waitFor();result.checks.push('Graph candidate endpoint navigation revalidates source');
    await page.getByRole('button',{name:'Close source',exact:true}).click();
    const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Download partial report JSON',exact:true}).click();
    const download=await downloadPromise;const file=await download.path(),exported=JSON.parse(fs.readFileSync(file));
    assert.deepEqual(exported.report,expected);assert.equal(exported.validation.source_revalidation,'VERIFIED_NOW');
    result.checks.push('JSON export exactly preserves original report, unknowns and validation receipt');
    for(const intent of ['scope','changes','unknowns','graph','evidence','limitations']){
      await page.getByLabel('Partial report explanation topic',{exact:true}).selectOption(intent);
      const response=page.waitForResponse(r=>new URL(r.url()).pathname.endsWith('/explain')&&r.request().method()==='POST');
      await page.getByRole('button',{name:'Explain selected topic',exact:true}).click();
      const explained=await (await response).json();assert.equal(explained.report_id,expected.report_id);
      assert.equal(explained.semantic_support,'NOT_ESTABLISHED');assert.equal(explained.inference_calls,0);
      for(const claim of explained.claims){let value={report:expected};for(const key of claim.json_pointer.slice(1).split('/'))value=value[key];assert.deepEqual(claim.value,value);}
      await page.getByRole('heading',{name:'Recorded topic: '+intent,exact:true}).waitFor();
    }
    result.checks.push('All six guided explanation topics bind exact report fields with semantic uncertainty');
    const htmlDownload=page.waitForEvent('download');await page.getByRole('button',{name:'Download partial report HTML',exact:true}).click();
    const htmlFile=await (await htmlDownload).path();const exportedHtml=fs.readFileSync(htmlFile,'utf8');
    const printPage=await context.newPage();await printPage.setContent(exportedHtml);
    assert.equal(await printPage.locator('script,iframe,img,object,form,a').count(),0);
    const recovered=JSON.parse(await printPage.locator('#complete-record').textContent());assert.deepEqual(recovered,exported);
    await printPage.close();result.checks.push('Printable HTML download preserves full JSON, original scope, unknowns and provenance without active content');
    await page.route('**/api/partial-reports/*/explain',route=>route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({detail:'Controlled explanation revalidation rejection'})}));
    await page.getByRole('button',{name:'Explain selected topic',exact:true}).click();
    await page.getByRole('alert').filter({hasText:'Controlled explanation revalidation rejection'}).waitFor();
    assert.equal(await page.getByRole('article',{name:'Selected partial report'}).count(),0);
    await page.unroute('**/api/partial-reports/*/explain');await open.click();await page.getByRole('heading',{name:'Review: '+first.case_id,exact:true}).waitFor();
    result.checks.push('Controlled failed explanation clears the old report/answer and recovers by fresh selection');

    await page.route('**/api/partial-reports/*/source?*',route=>route.fulfill({status:409,contentType:'application/json',body:JSON.stringify({detail:'Controlled stale-source rejection fixture'})}));
    await page.getByRole('button',{name:'Inspect source 1',exact:true}).click();
    await page.getByRole('alert').filter({hasText:'Controlled stale-source rejection fixture'}).waitFor();assert.equal(await excerpt.count(),0);
    await page.unroute('**/api/partial-reports/*/source?*');await page.getByRole('button',{name:'Close source',exact:true}).click();
    result.checks.push('Simulated 409 displays error and clears prior source; API rejection independently fixture-tested');
    await page.setViewportSize({width:390,height:844});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile document overflow');
    await page.getByRole('button',{name:'Inspect source 1',exact:true}).click();await excerpt.waitFor();
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile source overflow');
    result.checks.push('390px report/source layout has no document overflow');
    assert.equal(result.rows.length,saved.cases);assert.equal(result.rows.filter(x=>x.status==='UI_REPORT_VERIFIED').length,32);
    assert.equal(result.rows.reduce((n,r)=>n+(r.unknowns||0),0),371);
  }else{
    await page.getByText('Partial reports are disabled.',{exact:false}).waitFor();
    assert.equal(await page.getByRole('button',{name:/Open partial report/}).count(),0);
    result.checks.push('Default disabled view exposes no source or selectable reports');
  }
  assert.equal(result.errors.length,0);result.status='PASS';
})().catch(e=>{result.status='FAIL';result.errors.push(e.stack);process.exitCode=1}).finally(async()=>{
  if(browser)await browser.close();result.finished_at=new Date().toISOString();fs.writeFileSync(path.join(destination,'validation.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({status:result.status,cases:result.rows.length,checks:result.checks,errors:result.errors}));
});
