"""Cooperative stage-boundary control shared with process supervisors."""
from threading import Event,Lock
from time import monotonic


class InvestigationStopped(Exception):
    def __init__(self,status):
        self.status=status;self.run_id=None
        super().__init__('Investigation '+status.lower()+' at a safe stage boundary')


class RunControl:
    def __init__(self,seconds=900,clock=None,deadline=None,cancelled=None,publishing=None,lock=None):
        self.clock=clock or monotonic;self.deadline=deadline if deadline is not None else self.clock()+max(0,seconds)
        self.cancelled=cancelled or Event();self.publishing=publishing or Event();self.lock=lock or Lock()

    def _check(self):
        if self.publishing.is_set():return
        if self.clock()>=self.deadline:raise InvestigationStopped('TIMED_OUT')
        if self.cancelled.is_set():raise InvestigationStopped('CANCELLED')

    def check(self):
        with self.lock:self._check()

    def cancel(self):
        with self.lock:
            if self.publishing.is_set():return False
            self.cancelled.set();return True

    def begin_publication(self):
        # Once publication starts, keep one complete report rather than exposing
        # a cancelled run with only some evidence/findings written.
        with self.lock:self._check();self.publishing.set()
