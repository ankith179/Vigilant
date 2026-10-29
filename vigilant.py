"""VIGILANT command line: the same scoped services used by HTTP and MCP."""
import argparse
import json
import sys
from pathlib import Path
from database.store import Store
from investigation.service import InvestigationService, catalog


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database',help='SQLAlchemy database URL (otherwise VIGILANT_DB)')
    sub=parser.add_subparsers(dest='command',required=True)
    sub.add_parser('tools',help='List tool input/output contracts as JSON')
    call=sub.add_parser('call',help='Run a scoped tool, retain its evidence, print JSON')
    call.add_argument('tool');call.add_argument('--arguments',type=Path,required=True,help='JSON argument file')
    mcp=sub.add_parser('mcp',help='Serve MCP over local standard input/output')
    mcp.add_argument('--allow-record-updates',action='store_true')
    compare=sub.add_parser('compare',help='Run the existing deterministic base/head investigation')
    compare.add_argument('--repository',required=True,help='Imported repository identity')
    compare.add_argument('--base',required=True);compare.add_argument('--head',default='HEAD')
    args=parser.parse_args(argv)
    if args.command=='tools': print(json.dumps({'tools':catalog()},indent=2));return 0
    store=Store(args.database)
    try:
        if args.command=='mcp':
            from investigation.mcp import serve
            serve(store,args.allow_record_updates);return 0
        if args.command=='compare':
            from agents.workflow import analyze
            repo=store.get('repositories',args.repository)
            if not repo: raise ValueError('Imported repository not found')
            result=analyze(store,repo['path'],args.base,args.head,project=repo['project_id'],model='none')
        else:
            if args.arguments.stat().st_size>100_000: raise ValueError('Argument file exceeds 100 KB')
            result=InvestigationService(store).call(args.tool,json.loads(args.arguments.read_text(encoding='utf-8')))
        print(json.dumps(result,indent=2,ensure_ascii=False));return 0
    except (ValueError,OSError):
        print(json.dumps({'error':'Command rejected; check tool schema, scoped snapshot and source availability.'}),file=sys.stderr);return 2
    finally: store.engine.dispose()


if __name__=='__main__': raise SystemExit(main())
