# Cooperative job cancellation and deadlines — 25 October 2026

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
