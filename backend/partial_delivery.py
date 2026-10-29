"""Verified partial report presentation; source fidelity is not semantic truth."""
import html,json
from typing import Literal
from pydantic import BaseModel,ConfigDict,Field
from ingestion.models import digest
from investigation.staged import file_sha256

Intent=Literal['scope','changes','unknowns','graph','evidence','limitations']
class ExplanationInput(BaseModel):
    model_config=ConfigDict(extra='forbid')
    repository:str=Field(min_length=1,max_length=128)
    base_commit:str=Field(pattern=r'^[0-9a-f]{40}(?:[0-9a-f]{24})?$')
    head_commit:str=Field(pattern=r'^[0-9a-f]{40}(?:[0-9a-f]{24})?$')
    intent:Intent

TOPICS={
    'scope':('This report covers the pinned source scope below. Whole-project semantic coverage is not established.', ['scope','coverage']),
    'changes':('These are extracted-content observations and their declared denominators. They do not establish behavioral impact.', ['observed_outcomes','denominators','changed_artifact_observations']),
    'unknowns':('Unavailable artifact outcomes and source support remain unknown. Missing links or missing sides do not establish negative labels.', ['unknown_artifact_observations','source_unknowns','coverage']),
    'graph':('Both revision graphs retain candidate status and saved-page limits. Connectivity does not establish causal impact.', ['roles/base/graph','roles/head/graph']),
    'evidence':('These exact recorded excerpts have fresh source correspondence checks. Semantic support is not independently established.', ['evidence']),
    'limitations':('No reviewed obligation means no MISSING_TEST conclusion. Independent accuracy is not evaluated.', ['limitations','obligation_assessment','findings','quality_target'])}

def explain(loaded,intent):
    if intent not in TOPICS:raise ValueError('Unsupported explanation intent')
    report=loaded['report'];answer,paths=TOPICS[intent];claims=[]
    for path in paths:
        value=report
        for key in path.split('/'):value=value[key]
        claims.append({'claim_id':digest(report['report_id'],intent,path,value),'json_pointer':'/report/'+path,
                       'value':value,'support':'REPORT_FIELD_MATCH_ONLY'})
    return {'policy':'partial-report-explanation-v1','report_id':report['report_id'],'scope':report['scope'],
            'intent':intent,'answer':answer,'claims':claims,'validation':loaded['validation'],
            'presentation_source_sha256':file_sha256(__file__),'semantic_support':'NOT_ESTABLISHED',
            'reviewer_authentication':'NOT_ESTABLISHED','quality_target':'NOT_EVALUATED','inference_calls':0}

def export(loaded,format):
    if format not in {'json','html'}:raise ValueError('Unsupported partial export format')
    payload={**loaded,'delivery_provenance':{'policy':'partial-report-presentation-v1','source_sha256':file_sha256(__file__)}}
    if format=='json':return json.dumps(payload,ensure_ascii=False,indent=2),'application/json'
    report=loaded['report'];esc=lambda value:html.escape(str(value))
    block=lambda value:'<pre>'+esc(json.dumps(value,ensure_ascii=False,indent=2))+'</pre>'
    parts=['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">',
      '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\'">',
      '<title>VIGILANT partial development report</title><style>body{font:16px/1.5 system-ui;max-width:1000px;margin:24px auto;padding:16px;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f4;padding:12px}section{break-inside:avoid}h1,h2{color:#143d35}@media print{body{margin:0}}</style></head><body>',
      '<h1>VIGILANT partial development report</h1><p><strong>Independent 91% accuracy: NOT_EVALUATED.</strong> Candidates, unknowns and scoped observations are not verified semantic conclusions.</p>',
      '<p>Use browser Print → Save as PDF for a local printable copy.</p><h2>Report and pinned scope</h2>',
      '<p>Report ID: '+esc(report['report_id'])+'</p>',block(report['scope']),
      '<h2>Observed outcomes and denominators</h2>',block(report['observed_outcomes']),block(report['denominators']),
      '<h2>Unknown artifact outcomes</h2>',block(report['unknown_artifact_observations']),
      '<h2>Unavailable source support</h2>',block(report['source_unknowns']),
      '<h2>Coverage and unreviewed obligations</h2>',block(report['coverage']),block(report['obligation_assessment']),
      '<p>No reviewed obligation means no MISSING_TEST conclusion.</p><h2>Revision graph candidates</h2>']
    for role,data in report['roles'].items():
        graph=data['graph'];parts.extend(['<h3>'+esc(role)+' · '+esc(data['commit_id'])+'</h3>',
            '<p>Candidate relationships only; graph connectivity is not causal proof.</p>',
            block({'denominators':graph['denominators'],'next_offset':graph['next_offset'],'withheld_edges':graph['withheld_edges']}) if graph else '<p>Graph unavailable: no artifacts selected. Absence is not a negative link.</p>'])
    parts.append('<h2>Versioned source evidence</h2>')
    for item in report['evidence']:
        parts.extend(['<section><h3>'+esc(item['file'])+':'+esc(item['start_line'])+'–'+esc(item['end_line'])+'</h3>',
          '<p>Revision: '+esc(item['commit_id'])+'<br>Content hash: '+esc(item['content_hash'])+'<br>Evidence ID: '+esc(item['evidence_id'])+'</p>',
          '<pre>'+esc(item['quote'])+'</pre></section>'])
    parts.extend(['<h2>Limitations</h2>',block(report['limitations']),'<h2>Fresh validation receipt</h2>',block(loaded['validation']),
      '<h2>Complete report, graphs and provenance</h2><pre id="complete-record">'+esc(json.dumps(payload,ensure_ascii=False,indent=2))+'</pre></body></html>'])
    return '\n'.join(parts),'text/html'
