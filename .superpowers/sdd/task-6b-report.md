# Task 6b report — X3 hardening + window prep (E-25)

**Status:** DONE (verified post-hoc by controller from committed evidence; the implementer subagent's reply was lost to a wrapper timeout, its commit landed)
**Commit:** 7d79cc1 — mex: harden X3 structure task (maxlen 24, subtle single-pair corruption) — only mex/src/tasks.py + mex/tests/test_tasks.py.
**Controller-verified evidence:**
- diff audited: structure() now builds ok-lines balanced by construction (recursive splice), bad-lines half subtle one-pair flips (asserted unbalanced) / half legacy flips; labels ~50/50; (seed, n_val=200, n_test=500, n_train=30000) signature and rng scheme unchanged; _balanced untouched;
- suite 14/14 PASS incl. 3 new X3 tests (labels-match-checker, roughly-balanced, subtle-not-trivially-detectable) — run by controller after the timeout;
- data/mex/x3/{train,val,test}.txt regenerated (60000/400/1000 LINES = 30000/200/500 records), x3 tokens repacked (7:31:28) and control shards rebuilt 1s later;
- ME-D5 exact: control train+val 3,294,269 + 31,506 == sum(experts) (controller recomputation from bin sizes);
- E-25 pre-registration committed in this window; configs bumped to 12000 (c2510b0) by controller.
