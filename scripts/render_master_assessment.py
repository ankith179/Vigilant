"""Render one assessed task ledger and source-backed REA inventory; no parity claims."""
from pathlib import Path
from collections import Counter
import hashlib,json

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'reports/master-audit-20261025'
PIN='8e6a95788688439baeeec8e54c9b3e845226f79d'

def clean(value):return str(value).replace('|',' / ').replace('\n',' ')
def write(name,text):(ROOT/'docs'/name).write_text(text.strip()+'\n')

def main():
    assessment=json.loads((OUT/'assessment.json').read_text());tasks=assessment['tasks']
    columns=['id','priority','status','capability','dependencies','implementation','tests','observed_behavior','gap','acceptance']
    rows=[dict(zip(columns,t)) for t in tasks]
    (OUT/'task-register.json').write_text(json.dumps({'policy':assessment['policy'],'owner':assessment['owner'],'branch':None,'commit':None,'tasks':rows},indent=2)+'\n')
    pre='''# VIGILANT master task register — 25 October 2026

Source: reports/master-audit-20261025/assessment.json. This register covers the entire master directive; it does not mark a workstream complete merely because one fixture passes. Owner: local engineering agent, except real independent review and target-platform acceptance. Branch/commit: unavailable in this ZIP working copy. Use the source fingerprint and delivery checksum in PROJECT_BASELINE.md and the release record.

Statuses: NOT_STARTED, IN_PROGRESS, BLOCKED, IMPLEMENTED, VERIFIED, DEFERRED, NOT_APPLICABLE. REPORTED and UNKNOWN qualify evidence; NOT_EVALUATED qualifies metrics. IMPLEMENTED means bounded functionality exists; its documented missing acceptance still blocks broader completion. Historical evidence is retained under its original date.

'''
    table='| Task | Priority / status | Capability / dependencies | Implementation and observed behavior | Evidence and remaining gap | Acceptance |\n|---|---|---|---|---|---|\n'
    for t in rows:
        table+='| '+ ' | '.join(clean(x) for x in [t['id'],t['priority']+' / '+t['status'],t['capability']+'; depends on '+t['dependencies'],t['implementation']+' — '+t['observed_behavior'],t['tests']+' — '+t['gap'],t['acceptance']])+' |\n'
    write('VIGILANT_MASTER_TASK_REGISTER.md',pre+table+'''

Execution order: finish V022/V023 browser acceptance; resolve reproducible critical failures; then V015 cancellation/deadline controls and V008 lineage acceptance. V028 independent judgments and V029 final freeze remain external scientific prerequisites. V030 requires actual per-operation behavior checks before any full parity claim. No remote commit, push, submission or reviewer messaging is authorized by this ledger.
''')
    gap='''# VIGILANT integration gap matrix — 25 October 2026

Current assessed source and tests, linked to the task register. Test filenames identify actual behavioral fixtures exercised by the recorded full suite; they are not line/branch coverage percentages or independent accuracy evidence.

| Task / capability | Existing implementation | Observed integration | Actual test evidence | Missing functionality | Priority / acceptance |
|---|---|---|---|---|---|
'''
    for t in rows:
        gap+='| '+' | '.join(clean(v) for v in [t['id']+' '+t['capability'],t['implementation'],t['observed_behavior'],t['tests'],t['gap'],t['priority']+' — '+t['acceptance']])+' |\n'
    write('VIGILANT_INTEGRATION_GAP_MATRIX.md',gap)
    inventory=json.loads((OUT/'rea-inventory.json').read_text());assert not inventory['unresolved_imports'] and not inventory['duplicates']
    # These are functional analogues, not claims that REA's richer binary/runtime behavior is reproduced.
    equivalents={
      'inspect_artifact':('V013','investigation/service.py; investigation/staged_inspection.py','tests/test_staged_inspection.py','Bounded source excerpt analogue; REA archive/binary inventory semantics absent'),
      'compare_artifacts':('V009','investigation/staged_comparison.py','tests/test_staged_comparison.py','Pinned partial source comparison; full artifact/binary inventories and graph deltas differ'),
      'compare_application_versions':('V009','change_analysis/diff.py; agents/workflow.py','tests/test_integration.py','Source revision comparison; REA application graph comparison is not equivalent'),
      'find_changed_behavior':('V012','change_analysis/diff.py; knowledge_graph/graph.py','tests/test_audit_v2.py','Static changes and candidate impact; changed runtime behavior unverified'),
      'trace_feature':('V018','investigation/service.py::run_recipe','tests/test_investigation_tools.py','Retrieval/dependency recipe only; no native feature reconstruction'),
      'trace_application_feature':('V018','investigation/service.py::run_recipe','tests/test_investigation_tools.py','Source-assurance analogue; JS application/native feature projection absent'),
      'build_call_path':('V012','knowledge_graph/graph.py','tests/test_audit_v2.py','Typed bounded candidate paths; arbitrary native path reconstruction absent'),
      'trace_call_path':('V012','knowledge_graph/graph.py','tests/test_investigation_tools.py','Source candidate paths; binary provider semantics absent'),
      'get_call_graph':('V010','knowledge_graph/graph.py','tests/test_staged_graph.py','Candidate source graph; native graph parity not established'),
      'get_navigation_context':('V013','investigation/staged_inspection.py; frontend/src/PartialReports.jsx','tests/test_partial_report_api.py','Exact source revision selection; native document/address cursor context absent'),
      'list_unknowns':('V017','investigation/service.py','tests/test_investigation_tools.py::test_unknown_history_cas_and_source_resolution','Snapshot-scoped persisted unknowns; REA registry policy differs'),
      'record_unknown':('V017','investigation/service.py','tests/test_investigation_tools.py','Unknowns retained from tool outcomes; arbitrary manual record command absent'),
      'update_unknown':('V017','investigation/service.py','tests/test_investigation_tools.py::test_unknown_history_cas_and_source_resolution','Local append/CAS with source-linked caller attestation; no authenticated independent semantic closure'),
      'verify_unknown_resolution':('V017','investigation/service.py; consistency/obligations.py','tests/test_obligations.py','Source checks only; independent resolution verifier not implemented'),
      'build_reconstruction_obligation_ledger':('V016','consistency/obligations.py; consistency/search_inventory.py','tests/test_obligations.py; tests/test_search_inventory.py','Source-backed verification obligations; native/runtime reconstruction authority differs'),
      'evaluate_reconstruction_coverage':('V016','consistency/obligations.py; ingestion/coverage.py','tests/test_obligations.py','Scoped source coverage only; complete reconstruction/behavioral coverage unestablished'),
      'verify_reconstruction':('V016','consistency/obligations.py','tests/test_obligations.py','Requirement/test review only; reconstruction proof protocol absent'),
      'export_evidence_bundle':('V025','backend/exports.py; frontend/src/PartialReports.jsx','tests/test_release.py','Reports exported with source receipts; interoperable REA evidence bundle format absent'),
      'get_evidence_bundle':('V025','backend/exports.py; investigation/service.py','tests/test_release.py; tests/test_investigation_tools.py','Retained result/report retrieval; REA bundle/manifest semantics absent'),
      'import_evidence_bundle':('V013','evaluation/review_intake.py; agents/obligation_report.py','tests/test_review_intake.py; tests/test_obligation_report.py','Explicit reviewed intake only; generic evidence import/merge absent'),
      'inspect_evidence_bundle':('V025','investigation/service.py::inspect_retained_result','tests/test_investigation_tools.py::test_retained_payload_tampering_rejected','Retained source/identity checks; REA bundle input unsupported'),
      'inspect_analysis_view':('V022','backend/partial_reports.py; frontend/src/PartialReports.jsx','tests/test_partial_report_api.py','Bounded report view analogue; REA schema projections not implemented'),
      'inspect_analysis_settings':('V019','backend/app.py; PROJECT_STATE.json','tests/test_release.py','Limited workspace status/configuration; no equivalent full analysis-settings inspection'),
      'update_analysis_settings':('V019','backend/app.py; frontend/src/main.jsx','tests/test_frontend_api.py','Explicit local configuration only; no equivalent mutable analysis policy API')}
    for name,target in {'analyze_function':'inspect_artifact','binary_overview':'inspect_analysis_view','list_names':'inspect_artifact','list_procedures':'inspect_artifact','search_procedures':'trace_feature','search_strings':'trace_feature','procedure_callers':'trace_call_path','procedure_callees':'trace_call_path','procedure_references':'trace_call_path','xrefs':'trace_call_path','compare_functions':'compare_artifacts','compare_bundles':'compare_artifacts'}.items():
        t,implementation,tests,_=equivalents[target]
        equivalents[name]=(t,implementation,tests,'Source-assurance navigation/comparison analogue only; binary addresses, provider analysis and full REA operation semantics absent')
    cli_alias={'compare':'compare_application_versions','analyze':'binary_overview','trace':'trace_feature','function':'inspect_artifact','inspect':'inspect_artifact','search':'trace_feature','capabilities':'inspect_analysis_settings','providers':'inspect_analysis_settings','evidence-export':'export_evidence_bundle','evidence-import':'import_evidence_bundle','inspect-evidence-bundle':'inspect_evidence_bundle'}
    prompt_alias={'investigate_feature':'trace_feature','audit_residual_unknowns':'list_unknowns'}
    parity=[];tool_descriptions={r['name']:r['expected_behavior'] for r in inventory['rows'] if r['kind']=='tool'}
    for i,r in enumerate(inventory['rows'],1):
        name=r['name'];canonical=cli_alias.get(name,name.replace('-','_')) if r['kind']=='cli' else prompt_alias.get(name,name)
        if r['kind']=='cli' and canonical in tool_descriptions:r={**r,'expected_behavior':'Related tool contract (CLI handler equivalence still unverified): '+tool_descriptions[canonical]}
        entry={**r,'id':f'REA-{i:03d}','source_url':f'https://github.com/morluto/rea/blob/{PIN}/{r["path"]}#L{r["line"]}',
               'rea_behavior_verification':'SOURCE_CONTRACT_INSPECTED; RUNTIME_NOT_RUN','parity_established':False}
        if canonical in equivalents:
            task,implementation,tests,gap=equivalents[canonical]
            entry.update(applicability='APPLICABLE_PATTERN',status='IN_PROGRESS',task=task,implementation=implementation,actual_test_coverage=tests,
                         missing_functionality=gap,priority='P0' if task in {'V013','V016','V022'} else 'P1',acceptance='Test the applicable source-assurance behavior with exact revisions, invalid input, evidence failure and unknown retention; independently compare REA behavior before parity')
        elif name in {'setup','doctor','update','uninstall'}:
            entry.update(applicability='APPLICABLE_TOOLING',status='IN_PROGRESS',task='V031',implementation='Setup-Windows.ps1; scripts/restore_checkpoint.py; tools/browser/package.json',actual_test_coverage='tests/test_release.py; no unified doctor/update/uninstall parity checks',missing_functionality='Unified install/doctor/update rollback and managed uninstall parity absent',priority='P1',acceptance='Verify clean installation, diagnostic failures and reversible update/uninstall on declared platforms')
        elif any(word in canonical for word in ['browser','web_','javascript','electron','process','environment','desktop','managed','android','harmony','apple_application']):
            entry.update(applicability='DEFERRED_ADJACENT_RUNTIME_OR_PLATFORM',status='DEFERRED',task='V030',implementation='No equivalent advertised; source extraction is separately bounded',actual_test_coverage='No corresponding VIGILANT runtime parity test',missing_functionality='Runtime/bundle/device/environment observation needs a separately scoped isolated service and acceptance; source syntax is insufficient',priority='P2',acceptance='Approve applicable scope and safety boundary, retain unsupported results, then verify exact operation on real platform evidence')
        else:
            entry.update(applicability='OUTSIDE_DECLARED_SOURCE_ASSURANCE_SCOPE',status='NOT_APPLICABLE',task='V030',implementation='No equivalent; native debugger/decompiler/firmware/packet/device providers outside current requirements-code-tests workflow',actual_test_coverage='No VIGILANT parity test; excluded behavior',missing_functionality='Scope exclusion, not a parity pass; reassess if supported project scope expands',priority='P3',acceptance='Keep explicit exclusion; never advertise this REA operation as implemented')
        parity.append(entry)
    (OUT/'rea-parity-matrix.json').write_text(json.dumps({'reference_commit':PIN,'runtime_execution':'NOT_RUN','parity_established':False,'rows':parity},indent=2)+'\n')
    counts=Counter(r['kind'] for r in parity)
    intro=f'''# REA capability applicability and parity matrix — 25 October 2026

Reference: https://github.com/morluto/rea/commit/{PIN}, commit date 25 October 2026; package 6.7.0, MIT. The exact tree and inspected sources are retained in reports/master-audit-20261025/rea-source with upstream Git-blob identity checks. No REA repository code or tests were executed.

The canonical public contract arrays account for {counts['tool']} tool contracts and {counts['prompt']} MCP prompts; cliCommandNames.ts accounts for {counts['cli']} named one-shot commands. These 410 rows are a source-contract inventory, not a complete runtime feature proof: CLI global options/aliases, dynamic provider availability and transitive operation implementations still require behavior verification. Selected evidence/unknown/obligation/application services were inspected in addition to contracts. Every row states the verification limit. REA runtime support, provider availability and its own test suite remain NOT_RUN here. Full REA parity is NOT_ESTABLISHED.

Machine-readable full behavior descriptions, source hashes, exact lines, expected behavior, VIGILANT analogue, tests, missing behavior, priority, scope decision and acceptance are in reports/master-audit-20261025/rea-parity-matrix.json. VIGILANT fixture passes do not certify REA behavior. Similar names are not parity evidence. Adjacent runtime/platform operations are deferred for scope and isolation review; native debugger/decompiler providers are explicitly outside the declared source-assurance workflow.

Shared architecture evidence: src/application/CapabilityInventory.ts (host/target/provider availability), EvidenceBundleFiles.ts and EvidenceBundleCommands.ts (authenticated bundle validation and atomic publication), application/javascript/JavaScriptApplicationWorkflowService.ts (bound input comparison), ReconstructionObligationAuthority.ts (authority/owner/revision checks), investigation/UnknownEvidence.ts (immutable unknown mutation evidence), cli/commandCancellation.ts (awaited signal cleanup). VIGILANT counterparts and gaps appear in V002/V013/V015/V016/V017/V024/V025/V026. Language syntax extraction is not REA binary/provider semantic capability.

| ID / surface / capability | Source evidence | Expected behavior | Applicability / status | VIGILANT implementation and actual tests | Remaining gap / priority / acceptance |
|---|---|---|---|---|---|
'''
    for r in parity:
        expected=r['expected_behavior'];expected=expected[:200]+('… (full contract in JSON/source)' if len(expected)>200 else '')
        intro+='| '+' | '.join(clean(x) for x in [r['id']+' / '+r['kind']+' / '+r['name'],f'[{r["path"]}:{r["line"]}]({r["source_url"]})',expected,r['applicability']+' / '+r['status'],r['implementation']+'; '+r['actual_test_coverage'],r['missing_functionality']+'; '+r['priority']+'; '+r['acceptance']])+' |\n'
    write('REA_CAPABILITY_PARITY_MATRIX.md',intro)
    print(json.dumps({'tasks':len(rows),'rea_rows':len(parity),'parity_established':False,'applicability':dict(Counter(r['applicability'] for r in parity))}))

if __name__=='__main__':main()
