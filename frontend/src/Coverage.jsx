import React from 'react';

export default function Coverage({data}){
 if(!data)return <section aria-label="Investigation coverage"><h3>Investigation coverage</h3><p>This historical report has no complete Git inventory record. Coverage is not established.</p></section>;
 return <section aria-label="Investigation coverage"><h3>Investigation coverage</h3>
  <p>Excluded files and unresolved calls can contain relevant dependencies. Complete semantic and test coverage is not established.</p>
  {['base','head'].map(role=>{let c=data[role];return c&&<div key={role}><h4>{role} · {c.commit_id.slice(0,12)}</h4>
   <p>{c.discovered_files} discovered files · {c.extracted_files} extracted · {c.parse_failures.length} parse failures · {c.unresolved_or_unmodelled_calls} unresolved or unmodelled calls</p>
   <div className="table-wrap"><table><thead><tr><th>Language</th><th>Discovered</th><th>Eligible</th><th>Extracted</th><th>Parse failures</th></tr></thead><tbody>{Object.entries(c.languages).map(([name,n])=><tr key={name}><td>{name}</td><td>{n.discovered}</td><td>{n.eligible}</td><td>{n.extracted}</td><td>{n.parse_failures}</td></tr>)}</tbody></table></div>
   <p>{c.test_artifacts} test artifacts · {c.requirement_artifacts} requirement artifacts · {c.candidate_matched_calls} calls with candidate relationships</p>
   {c.compiler_parse_files!==undefined&&<p>{c.compiler_parse_files} files checked by a native compiler · {c.compiler_reference_edges} compiler-reference edges under snapshot assumptions. Project build configuration remains unverified.</p>}
   {!!c.compiler_unavailable_files?.length&&<p>Compiler unavailable: {c.compiler_unavailable_files.join(', ')}</p>}
   {!!c.parse_failures.length&&<p>Parse failures: {c.parse_failures.join(', ')}</p>}
   <details><summary>Exclusions and gaps</summary><pre>{JSON.stringify({exclusions:c.exclusions_by_reason,eligible_but_not_extracted:c.eligible_but_not_extracted},null,2)}</pre></details>
  </div>})}
 </section>;
}
