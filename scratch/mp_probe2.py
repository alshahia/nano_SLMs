"""Replicate prepare_data pool path with faulthandler tracing."""
import faulthandler, sys, json, time
sys.path.insert(0, "diacritizer\scripts")
faulthandler.dump_traceback_later(45, exit=True)
import prepare_data as P
t0 = time.time()
try:
    st = P.process(None, {"abdou_valid"})
except BaseException as e:
    print("EXC", repr(e))
print("DONE", round(time.time() - t0, 1), "s")
