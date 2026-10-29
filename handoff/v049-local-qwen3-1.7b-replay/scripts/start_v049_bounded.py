"""Start or supervise one finite local replay; never restart automatically."""
import json
from pathlib import Path
import subprocess
import sys
import time

WORK = Path(__file__).resolve().parent
PYTHON = Path(r'C:\Users\Ankith\Downloads\vigilant project code\.venv\Scripts\python.exe')
STATE = WORK/'v049-bounded-process.json'
if '--supervise' in sys.argv:
    cmd = [str(PYTHON), '-X', 'utf8', str(WORK/'v049_combined_snapshot_replay.py')]
    with (WORK/'v049-bounded.stdout.log').open('wb') as stdout, (WORK/'v049-bounded.stderr.log').open('wb') as stderr:
        process = subprocess.Popen(cmd, cwd=WORK.parent, stdout=stdout, stderr=stderr,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
        state={'status':'RUNNING','pid':process.pid,'started_epoch':time.time(),'deadline_seconds':7200,
               'command':cmd,'new_attempts_allowed':0}
        STATE.write_text(json.dumps(state,indent=2),encoding='utf-8')
        try:
            code=process.wait(timeout=7200)
            state.update(status='COMPLETED' if code==0 else 'FAILED',exit_code=code)
        except subprocess.TimeoutExpired:
            process.terminate();process.wait(timeout=30)
            state.update(status='DEADLINE_EXCEEDED',exit_code=process.returncode)
        state['finished_epoch']=time.time()
        STATE.write_text(json.dumps(state,indent=2),encoding='utf-8')
else:
    if STATE.exists():
        raise SystemExit('Inspect existing process state before launching another replay')
    process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'--supervise'],cwd=WORK.parent,
                             creationflags=subprocess.CREATE_NO_WINDOW)
    print(json.dumps({'supervisor_pid':process.pid,'state_file':str(STATE),'maximum_runtime_seconds':7200}))
