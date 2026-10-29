# Agent job cancellation and deadlines — 26 October 2026

V015 is **IN_PROGRESS**. File-backed SQLite jobs run in a spawned process. The API worker supervises the process, checks its monotonic deadline, and escalates cancellation through a short cooperative grace period, terminate, then kill. On Windows the worker is contained in a Job Object configured to terminate descendants; on POSIX it starts a new process group and termination is sent to that group. A child-process test verifies Windows worker and descendant termination. Final evidence, findings, graph changes, and the completed report are committed as one SQLite transaction. The job record is finalized separately by the parent, so startup recovery reconciles a report committed just before a worker or server exit.

Before startup recovery, file-backed SQLite servers acquire an OS sidecar lock beside the database. A second process cannot own the same database concurrently. The lock releases on normal shutdown and is reclaimed by the OS after process exit. This is a single-server guard, not multi-server coordination; use one application process until a broker/lease design is implemented.

`POST /api/analysis/run` accepts a strict integer `timeout_seconds` from 1 to 3,600, default 900. The original UTC deadline is persisted and queue time counts toward the budget. Process supervision converts the remaining persisted UTC budget to a monotonic deadline. A completed report found during restart is linked as the result; a stopped report remains partial; a running job without a terminal report is marked failed and never replayed automatically.

`POST /api/analysis/jobs/{job_id}/cancel` uses the existing workspace-token guard. Missing or non-job IDs return 404; active records not owned by this server return 409. Repeated cancellation of a terminal job returns the existing record. Final publication already in progress cannot be cancelled through the API.

| State / action | File-backed SQLite worker | In-memory, non-SQLite, or custom thread runner |
|---|---|---|
| QUEUED → cancel | Persist CANCELLED immediately; body does not start. Its queue placeholder retains its capacity slot until drained. | Same. |
| RUNNING → cancel | Persist CANCEL_REQUESTED, signal the worker, allow a short grace period, then terminate/kill the worker if needed. Preserve an explicit partial result. | Cooperative stop at the next safe stage boundary; an in-flight call may continue until it returns. |
| Deadline expires | Parent supervisor stops the worker with bounded escalation. | The control is observed at the next safe stage boundary. |
| Restart with CANCEL_REQUESTED | Finalize CANCELLED; interrupted outcome remains unknown. Never replay. | Same. |
| Restart with RUNNING | Reconcile a committed complete/stopped report when present; otherwise mark FAILED. Never replay. | Mark FAILED rather than replay a possibly billed call. |
| Restart with QUEUED | Resume known-unstarted work using its original deadline; expired work becomes TIMED_OUT. | Same. |

The file-backed worker path is covered by process tests, including cancellation after a marker proves the child entered the runner, deadline termination, child-process-tree cleanup, cross-process database lock contention, abrupt worker exit, and server-process termination while a worker is active. On Windows, the server-kill test verifies that Job Object closure kills the worker subtree, the sidecar lock is released, startup marks the interrupted job FAILED, and no runner is replayed. A mocked test also confirms POSIX TERM/KILL escalation still reaches the group after its leader exits. Forced worker termination closes the pipe; the parent skips forced-stop pipe reads and treats broken-pipe errors as missing worker output. Atomic publication and rollback are covered by the focused regression suite. Latest evidence: `reports/job-controls-20261026/VERIFICATION.md` and `reports/job-controls-20261026/tests-v015-final-verified.xml`.

## Limits

Windows process-tree containment and one server-kill/restart/no-replay recovery path are verified for the tested fixtures. POSIX process-group TERM/KILL escalation has mocked unit coverage for a leader exiting before its child; actual POSIX execution was unavailable in this Windows acceptance. Git/compiler/model-specific descendants and hostile breakaway behavior have not each been tested. The parent still depends on operating-system scheduling and database availability, so strict wall-clock completion is not established. The sidecar lock rejects multiple server owners; it does not coordinate multiple workers. In-memory and non-SQLite backends retain cooperative cancellation. No security certification is implied.

No model calls or label changes occurred. The 95% assurance target remains NOT_EVALUATED; release readiness remains NOT MET.

## 25 October cooperative baseline

The original cooperative-only behavior and acceptance evidence are preserved in `docs/archive/JOB_CONTROLS-20261025.md` and `reports/job-controls-20261025/`.

---

## Prior detailed acceptance record — 25 October 2026

The remaining text in this section is retained as the previous baseline. Statements that all stops are cooperative or that final report publication is not atomic are superseded by the 26 October scope above. The complete original file is preserved at `docs/archive/JOB_CONTROLS-20261025.md`.

`POST /api/analysis/run` now accepts `timeout_seconds`, a strict integer from 1 to
3,600, default 900. The accepted job stores the original UTC `deadline_at`, request
budget and `COOPERATIVE_STAGE_BOUNDARY` policy. Queue time counts toward the budget.
The process uses monotonic time while running; restart recovery computes remaining
time from the persisted UTC deadline rather than granting a fresh budget.

`POST /api/analysis/jobs/{job_id}/cancel` uses the existing workspace-token guard.
It accepts only actual job records owned by this server. A missing/non-job ID is
404; an active record not owned by this process is 409. Repeating a cancellation on
a terminal job returns that existing record. No source files, historical reports,
benchmarks, labels or completed report contents are modified by this operation.

| State / action | Behavior |
|---|---|
| QUEUED → cancel | Persist CANCELLED immediately; the body never starts. Its lightweight queue placeholder retains its capacity slot until the worker drains it. This bounds memory during repeated queue/cancel requests. |
| RUNNING → cancel | Persist CANCEL_REQUESTED. The active operation finishes, then the next safe check persists CANCELLED. A request is not proof that execution has already stopped. |
| Budget expires | Persist TIMED_OUT when the worker observes its next safe check; queued expired work is rejected before analyze starts. There is no watchdog that falsely marks an in-flight operation stopped. |
| Final publication already started | Cancellation returns 409. Cooperative stopping cannot split the final publication into a cancelled record and a partially published result. Completion can win a late cancellation race. |
| Restart with CANCEL_REQUESTED | Finalize CANCELLED with the interrupted operation outcome explicitly unknown; never replay it. |
| Restart with RUNNING | Retain existing behavior: mark FAILED rather than replay a possibly billed call. |
| Restart with QUEUED | Resume only known-unstarted work, preserving its deadline; expired work becomes TIMED_OUT without analysis. |

Completed, failed, cancelled and timed-out jobs are terminal. Job metrics expose
the new statuses. Dashboard controls expose the budget, cancellation request and
terminal status; cancellation applies to the dashboard's tracked job. Any owned
job can be cancelled through the API. Comparison chat stops polling on CANCELLED
or TIMED_OUT rather than relabelling the result RUNNING. Job-history cancellation
controls beyond the tracked dashboard job remain future UI work.

The shared `RunControl` checks before and after workflow stages, before provider
initialization and before final publication. Encoder preparation is a stage when
semantic retrieval is requested. A stopped workflow retains its own partial run ID,
scope, stage trajectory, quote metrics and explicit partial-results flag; the job
links it as `partial_run_id`, never as a completed `result_run_id`. Already completed
ingestion/graph/retrieval writes remain in the selected working database. Stopping
does not roll them back or manufacture a complete investigation report.

Final publication is protected from cooperative stops, not made into a new database
transaction. Process death or a persistence error can still leave failed partial
writes. Independent crash/checkpoint recovery and multiworker ownership are not
established. Use one application process and the existing single analysis worker.

## Actual boundary

This is **cooperative cancellation**, not thread killing, subprocess-tree termination
or a hard wall-clock guarantee. Git, parser/compiler, model loading and inference
operations already in flight retain their own limits/retries. Cancellation/deadline
overrun can last until that operation returns. External operations are not claimed
aborted, and model calls are never replayed merely to recover a stop. A server
shutdown still waits for its worker; stronger process isolation and hard deadlines
remain a separate V015 acceptance item. Existing direct `analyze`/CLI/watch callers
keep their prior unbounded budget unless a caller explicitly supplies RunControl.
CLI/watch commands do not yet expose custom budget flags. The API always supplies
the validated job budget, including its default 900 seconds.

Evidence: reports/job-controls-20261025/VERIFICATION.md, tests-final.xml, guard-tests.log,
browser-controls-final/ and browser-regression/. Lifecycle browser outcomes use a clearly
labelled cooperative worker fixture through the actual production UI/API; they are
not independent software-assurance predictions or model-quality measurements.
