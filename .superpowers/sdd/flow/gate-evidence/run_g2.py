
import json, urllib.request, pathlib
BASE = "http://127.0.0.1:3010"
out = pathlib.Path(".superpowers/sdd/flow/gate-evidence"); out.mkdir(parents=True, exist_ok=True)
log = []
def call(name, method, path, body=None):
    req = urllib.request.Request(BASE+path, method=method,
        data=None if body is None else json.dumps(body).encode(),
        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            code, data = r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        code, data = e.code, json.loads(e.read())
    log.append({"check": name, "method": method, "path": path, "status": code, "response": data})
    print(f"{name}: HTTP {code}")
    return code, data

def graph(name="gate-demo", nodes=None, edges=None):
    return {"schema":"flow/0.1","meta":{"name":name},"graph":{
      "nodes": nodes or [
        {"id":"n1","kind":"dataset","label":"TheGamingMahi/TinyCode","props":{},"position":{"x":0,"y":0}},
        {"id":"n2","kind":"prepare","props":{"rows":3000,"val_fraction":0.02,"min_chars":80},"position":{"x":200,"y":0}},
        {"id":"n3","kind":"tokenize","props":{"seq_len":256,"vocab":32000},"position":{"x":400,"y":0}},
        {"id":"n4","kind":"train","props":{"preset":"Small (~12M, smoke)","steps":200,"lr_preset":"Pretrain 4e-4"},"position":{"x":600,"y":0}}],
      "edges": edges or [
        {"id":"e1","from":"n1","to":"n2","fromPort":"cleaned","toPort":"raw-dir"},
        {"id":"e2","from":"n2","to":"n3","fromPort":"cleaned-dir","toPort":"cleaned-dir"},
        {"id":"e3","from":"n3","to":"n4","fromPort":"shard-dir","toPort":"shard-dir"}]}}

# (a) valid chain: validate ok + save
g = graph()
_, v = call("2a-validate-valid","POST","/api/validate",g)
assert v["ok"] is True, v
call("2a-save-valid","PUT","/api/flows/gate-demo",g)
# (b) dataset->train direct (port mismatch) must be invalid
g_b = graph(); g_b["graph"]["nodes"].append({"id":"n5","kind":"train","props":{"preset":"Pilot (~110M)","steps":10,"lr_preset":"Pretrain 4e-4"},"position":{"x":0,"y":200}}); g_b["graph"]["nodes"][-1]["id"]="n5"
g_b["graph"]["edges"].append({"id":"e4","from":"n1","to":"n5","fromPort":"cleaned","toPort":"shard-dir"})
_, v = call("2b-port-mismatch","POST","/api/validate",g_b)
assert v["ok"] is False, v
# (c) train with no tokenize upstream -> missing-input
g_c = {"schema":"flow/0.1","meta":{"name":"gate-demo"},"graph":{"nodes":[
  {"id":"n4","kind":"train","props":{"preset":"Small (~12M, smoke)","steps":200,"lr_preset":"Pretrain 4e-4"},"position":{"x":0,"y":0}}],
  "edges":[]}}
_, v = call("2c-missing-shard","POST","/api/validate",g_c)
assert v["ok"] is False, v
# (d) reserved name smoke
g_d = graph("smoke")
_, v = call("2d-reserved-name","POST","/api/validate",g_d)
assert v["ok"] is False and any("reserved" in e for e in v["errors"]), v
# (e) rows > 500k
g_e = graph(); g_e["graph"]["nodes"][1]["props"]["rows"] = 900000
_, v = call("2e-rows-cap","POST","/api/validate",g_e)
assert v["ok"] is False and any("cap" in e for e in v["errors"]), v
# (f) branching graph
g_f = graph(); g_f["graph"]["edges"].append({"id":"e5","from":"n2","to":"n1","fromPort":"cleaned-dir","toPort":"raw-dir"})
# cycle detection / linear-chain: expect some error
_, v = call("2f-branching-or-cycle","POST","/api/validate",g_f)
assert v["ok"] is False, v
# extra: status + nodes endpoint
call("extra-status","GET","/api/run/status")
call("extra-nodes","GET","/api/nodes")
(out/"g2-http-gates.json").write_text(json.dumps(log, indent=1))
print("GATE-EVIDENCE-SAVED")
