from pathlib import Path
from datetime import datetime,timezone
import json,uuid,platform,sys,psutil
ROOT=Path(__file__).resolve().parents[1]
def save_run(kind,payload):
 rid=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8];path=ROOT/'experiments'/kind/rid;path.mkdir(parents=True,exist_ok=False)
 # Optional telemetry must not discard a completed experiment in restricted runtimes.
 try:memory={'rss_mib_at_save':psutil.Process().memory_info().rss/1048576}
 except (psutil.Error,OSError) as exc:memory={'rss_mib_at_save':None,'memory_measurement_error':type(exc).__name__}
 result={'run_id':rid,'kind':kind,'python':sys.version,'platform':platform.platform(),**memory,**payload};(path/'results.json').write_text(json.dumps(result,indent=2,ensure_ascii=False));return path,result
