import React, {useState} from 'react';

// Display persisted structural edges only. Similarity candidates are not proof.
export default function Graph({data, onSelect}) {
  const [relation, setRelation] = useState('ALL');
  const allEdges = data?.edges || [];
  const byId = new Map((data?.nodes || []).map(node => [node.artifact_id, node]));
  const edges = allEdges.filter(edge => relation === 'ALL' || edge.relation_type === relation);
  const visibleEdges = edges.slice(0, 24);
  const ids = [...new Set(visibleEdges.flatMap(edge => [edge.source_artifact, edge.target_artifact]))];
  const nodes = ids.filter(id => byId.has(id)).map(id => byId.get(id));
  const position = new Map(nodes.map((node, i) => [node.artifact_id, {
    x: 95 + (i % 5) * 168, y: 55 + Math.floor(i / 5) * 112,
  }]));
  const label = node => node?.symbol || node?.file || node?.artifact_type || 'Unknown endpoint';
  const color = node => node.artifact_type === 'api' ? '#b9681b'
    : node.artifact_type === 'commit' ? '#784dab'
    : node.artifact_type?.includes('test') ? '#436fa0' : '#17766c';
  const missing = ids.filter(id => !byId.has(id)).length;
  return <>
    <div className="section-head">
      <h2>Snapshot relationships</h2>
      <label className="graph-filter">Relationship
        <select aria-label="Relationship" value={relation} onChange={event => setRelation(event.target.value)}>
          <option value="ALL">All relationships</option>
          {[...new Set(allEdges.map(edge => edge.relation_type))].sort().map(type =>
            <option key={type}>{type}</option>)}
        </select>
      </label>
    </div>
    <p className="muted">Loaded {allEdges.length} recorded edges{data?.truncated ? ' (snapshot has more)' : ''}.
      Diagram shows up to 24 matching edges; the table contains all {edges.length} loaded matches.
      Arrows point from source to target. Select a node or relationship for provenance.</p>
    {missing > 0 && <p className="muted">{missing} endpoints have no node in this snapshot,
      for example deleted artifacts. Their original IDs remain in the relationship table.</p>}
    {nodes.length > 0 ? <svg role="img" aria-label="Repository traceability graph"
      viewBox={`0 0 870 ${Math.max(200, Math.ceil(nodes.length / 5) * 112 + 35)}`}>
      <defs><marker id="graph-arrow" viewBox="0 0 10 10" refX="9" refY="5"
        markerWidth="6" markerHeight="6" orient="auto-start-reverse">
        <path d="M 0 0 L 10 5 L 0 10 z" fill="#78968c"/>
      </marker></defs>
      {visibleEdges.map((edge, i) => {
        const start = position.get(edge.source_artifact), end = position.get(edge.target_artifact);
        if (!start || !end) return null;
        const length = Math.hypot(end.x-start.x, end.y-start.y) || 1;
        const dx = (end.x-start.x)/length*21, dy = (end.y-start.y)/length*21;
        return <line key={edge.id || i} data-graph-edge="true" x1={start.x+dx} y1={start.y+dy}
          x2={end.x-dx} y2={end.y-dy} stroke="#78968c" strokeWidth="1.4" markerEnd="url(#graph-arrow)">
          <title>{label(byId.get(edge.source_artifact))} → {edge.relation_type} → {label(byId.get(edge.target_artifact))}</title>
        </line>;
      })}
      {nodes.map(node => {
        const {x, y} = position.get(node.artifact_id);
        return <g key={node.artifact_id} data-graph-node="true" role="button"
          aria-label={`Inspect ${label(node)}`} tabIndex="0" onClick={() => onSelect(node)}
          onKeyDown={event => {if (['Enter', ' '].includes(event.key)) {event.preventDefault(); onSelect(node);}}}>
          <title>{label(node)} · {node.artifact_type}</title>
          <circle cx={x} cy={y} r="18" fill={color(node)}/>
          <text x={x} y={y+38} textAnchor="middle" fontSize="10" fill="#334843">
            {label(node).split('/').pop().slice(0, 23)}</text>
          <text x={x} y={y+52} textAnchor="middle" fontSize="9" fill="#657a70">{node.artifact_type}</text>
        </g>;
      })}
    </svg> : <p className="empty">No recorded relationships for this selection.</p>}
    {edges.length > 0 && <div className="table-wrap"><table aria-label="Graph relationships">
      <thead><tr><th>Source</th><th>Relationship</th><th>Target</th><th>Method</th></tr></thead>
      <tbody>{edges.map((edge, i) => <tr key={edge.id || i} tabIndex="0"
        onClick={() => onSelect(edge)} onKeyDown={event => event.key === 'Enter' && onSelect(edge)}>
        <td title={edge.source_artifact}>{label(byId.get(edge.source_artifact))}</td>
        <td>{edge.relation_type}</td><td title={edge.target_artifact}>{label(byId.get(edge.target_artifact))}</td>
        <td>{edge.method || 'Recorded relation'}</td>
      </tr>)}</tbody>
    </table></div>}
  </>;
}
