"""Portable report exports; browser printing provides PDF without another service."""
import csv
import html
import io
import json


def export(report,format):
    if format=='json':return json.dumps(report,indent=2),'application/json'
    if format=='csv':
        out=io.StringIO(newline='');writer=csv.writer(out)
        writer.writerow(['status','rule','reason','affected_artifacts','evidence_ids'])
        for finding in report.get('findings',[]):
            values=[finding.get(k,'')for k in ['status','rule','reason','affected_artifacts','evidence_ids']]
            values=[json.dumps(v)if isinstance(v,(dict,list))else str(v)for v in values]
            # Avoid spreadsheet formula execution when exporting repository text.
            writer.writerow(["'"+v if v.lstrip().startswith(('=','+','-','@'))else v for v in values])
        return out.getvalue(),'text/csv'
    if format!='html':raise ValueError('Unsupported export format')
    esc=lambda x:html.escape(str(x))
    model=report.get('model',{}).get('decision',{})
    content=['<!doctype html><html lang="en"><meta charset="utf-8"><title>VIGILANT report</title>',
             '<style>body{font:16px/1.5 system-ui;max-width:960px;margin:32px auto;padding:20px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f3f5f7;padding:12px}section{break-inside:avoid}h1,h2{color:#12364d}@media print{body{margin:0}}</style>',
             '<h1>VIGILANT evidence report</h1>',f'<p>Run: {esc(report.get("run_id",""))}<br>Revision: {esc(report.get("commit_id",""))}</p>',
             f'<h2>Model decision: {esc(model.get("decision","Not available"))}</h2>',
             '<p>Source fidelity does not prove semantic correctness. Rule findings are review hypotheses.</p>',
             '<p>Use your browser’s Print → Save as PDF to export this document.</p><h2>Rule findings</h2>']
    for f in report.get('findings',[]):content.append(f'<section><h3>{esc(f.get("status",""))}</h3><p>{esc(f.get("reason",""))}</p><pre>{esc(json.dumps(f,indent=2))}</pre></section>')
    content.append('<h2>Versioned evidence</h2>')
    for e in report.get('evidence',[]):content.append(f'<section><h3>{esc(e.get("file",""))}:{esc(e.get("start_line",""))}–{esc(e.get("end_line",""))}</h3><p>Commit: {esc(e.get("commit",""))}<br>Hash: {esc(e.get("content_hash",""))}</p><pre>{esc(e.get("quote",""))}</pre></section>')
    content.append('<h2>Full record</h2><pre>'+esc(json.dumps(report,indent=2))+'</pre></html>')
    return '\n'.join(content),'text/html'
