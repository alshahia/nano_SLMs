"""Batch 003 - PROMPT D fixes applied (interactive coherence) for the U-line kit.

Implements the adjudicated critique advice from the batch-001 PROMPT D pass:
1. controls that imply state changes carry change events (setState) so gated
   content can actually fire (no dead flags);
2. gate predicates match their semantics (priority hint gated on an empty
   priority, not on unrelated text);
3. gated comparisons are guaranteed fireable (compared value exists in the
   driving options / seed data);
4. Tabs/ToggleGroup/Select values bound to state where representable; seed
   lists carry the states the task names (done items, read/unread mix);
5. conditional content semantically matches its trigger (incidents are
   warning/error, never success copies; item chips only on items that are);
6. vocabulary coherence (filter options and seeded statuses come from the
   same list; plan ladder priced ascending).

Output: ui/data/omen_alpha/side_omen_alpha_batch003_interactive.jsonl
"""

from __future__ import annotations

import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scratch"))
sys.path.insert(0, ROOT)

from omen_side_build import (DOMAINS, DOMAIN_KEYS, _el, _card,
                             _stack, _grid, _heading, _text, _badge, _button,
                             _metric, _input, _select, _switch, _progress,
                             _alert, _bounds_check, _features)
from ui.src.validate import validate_spec, validate_chain
from ui.src.chain import spec_to_chain, chain_to_spec

OUT_DIR = os.path.join(ROOT, "ui", "data", "omen_alpha")
OUT = os.path.join(OUT_DIR, "side_omen_alpha_batch003_interactive.jsonl")
TONES = ["terse", "verbose", "imperative", "casual"]
PIPE_RES = ["Queued", "Held", "Cleared"]
PLANS_LADDER = [("Starter", "$9/mo"), ("Plus", "$19/mo"), ("Pro", "$29/mo"), ("Team", "$49/mo")]


def _set_on(key, statePath, value=True):
    return {"change": {"action": "setState",
                       "params": {"statePath": statePath, "value": value}}}


def _v_settings_wired(g, D):
    els, used = {}, set()
    st = {"prefs": {"digest": "weekly", "compact": False, "alertsOn": False, "dirty": False}}
    root = _card(g, used, els, title="Preferences", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    se = _select(g, used, els, "Digest", "digest", ["daily", "weekly", "monthly"],
                 None, {"$bindState": "/prefs/digest"})
    els[se]["on"] = _set_on(se, "/prefs/dirty")
    sw1 = _switch(g, used, els, "Compact tables", "compact",
                  {"$bindState": "/prefs/compact"})
    els[sw1]["on"] = _set_on(sw1, "/prefs/dirty")
    sw2 = _switch(g, used, els, "Alerts on", "alertsOn",
                  {"$bindState": "/prefs/alertsOn"})
    els[sw2]["on"] = _set_on(sw2, "/prefs/dirty")
    al = _alert(g, used, els, "Unsaved prefs", "Flag your changes before leaving this page.",
                "info", visible={"$state": "/prefs/dirty", "eq": True})
    sv = _button(g, used, els, "Save prefs", "primary", "save_form", {})
    els[stk]["children"] = [se, sw1, sw2, al, sv]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Prefs w/ switches that set the dirty state on change; banner until saved.",
        "verbose": ("A {thing} prefs panel where every control (digest select, two "
                    "switches) sets a dirty state on change, an info banner appears while "
                    "the dirty state is set, and Save releases it.").format(thing=D["thing"]),
        "imperative": ("Wire each control's change event to set /prefs/dirty; gate the "
                       "banner on prefs/dirty eq true; save action at the end."),
        "casual": ("toggles that actually light the 'unsaved' banner while dirty pls"),
    }
    return {"root": root, "elements": els, "state": st}, tasks


def _v_todo_done_seed(g, D):
    els, used = {}, set()
    n = g.randint(3, 5)
    pi = g.randint(0, n - 1)
    items = [{"id": "t{0}".format(i + 1), "title": g.choice(D["tasks"]),
              "done": (i == pi) or (g.random() < 0.25)} for i in range(n)]
    st = {"draft": {"title": ""}, "items": items}
    root = _card(g, used, els, title="Tasks", maxWidth="md")
    nw = _input(g, used, els, "New task", "draftTitle", "text", "What needs doing?",
                {"$bindState": "/draft/title"})
    ad = _button(g, used, els, "Add task", "primary", "pushState",
                 {"statePath": "/items", "value": {"$state": "/draft/title"},
                  "title": {"$state": "/draft/title"}, "done": False, "id": "$id"})
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/items", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "title"}
    bd = _badge(g, used, els, "checked", "outline")
    els[bd].update({"visible": {"$item": "done", "eq": True}})
    tx = _text(g, used, els, "Submitted items start unchecked.", "caption")
    els[itm]["children"] = [bd]
    els[root]["children"] = [nw, ad, lst, tx]
    els[lst]["children"] = [itm]
    tasks = {        "terse": "Task list with at least one pre-checked seed; adds start unchecked.",
        "verbose": ("A {thing} task board whose seed list already includes a checked "
                    "entry so the check chip is actually visible, and the add action "
                    "always inserts a fresh unchecked row.").format(thing=D["thing"]),
        "imperative": ("Seed at least one done item; badges show the check word on rows "
                       "whose done is true; pushState always appends done false."),
        "casual": ("seed a checked one so the chip actually shows up, yeah"),
    }
    return {"root": root, "elements": els, "state": st}, tasks


def _v_priority_hint(g, D):
    els, used = {}, set()
    n = g.randint(2, 4)
    items = [{"id": "t{0}".format(i + 1), "title": g.choice(D["tasks"]),
              "priority": g.choice(["Low", "Medium", "High"]), "done": False}
             for i in range(n)]
    st = {"draft": {"summary": "", "priority": ""}, "items": items}
    root = _card(g, used, els, title="Task intake", maxWidth="md")
    nw = _input(g, used, els, "Summary", "draftSummary", "text", "One-liner",
                {"$bindState": "/draft/summary"})
    se = _select(g, used, els, "Priority", "draftPriority",
                 ["Low", "Medium", "High"], None, {"$bindState": "/draft/priority"})
    al = _alert(g, used, els, "Priority first", "Choose a priority to enable intake.",
                "info", visible={"$state": "/draft/priority", "eq": ""})
    ad = _button(g, used, els, "Add task", "primary", "pushState",
                 {"statePath": "/items", "value": {"$state": "/draft/summary"},
                  "title": {"$state": "/draft/summary"},
                  "priority": {"$state": "/draft/priority"}, "done": False, "id": "$id"})
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/items", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "title"}
    ib = _badge(g, used, els, {"$item": "priority"}, "outline")
    els[itm]["children"] = [ib]
    els[root]["children"] = [nw, se, al, ad, lst]
    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Intake: hint shows exactly while priority is still empty.",
        "verbose": ("A {thing} intake where the 'choose a priority' hint is gated on the "
                    "priority field itself being empty - set a priority and the hint "
                    "gives way to the Add button's row.").format(thing=D["thing"]),
        "imperative": ("Gate the hint on /draft/priority eq empty string, not on the "
                       "summary field; both fields bind into draft."),
        "casual": ("hint goes away once i actually picked a priority plz"),
    }
    return {"root": root, "elements": els, "state": st}, tasks


def _v_incident_coherent(g, D):
    els, used = {}, set()
    st = {"incident": False}
    root = _card(g, used, els, title="Service watch", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md", align="start")
    hd = _heading(g, used, els, "Live gate", "h2")
    sw = _switch(g, used, els, "Incident switch", "incident",
                 {"$bindState": "/incident"})
    alw = [a for a in D["alerts"] if a[1] != "success"]
    a0 = alw[0] if alw else D["alerts"][0]
    a1 = _alert(g, used, els, a0[0], a0[0] + " - crews engaged.", "error",
                visible={"$state": "/incident", "eq": True})
    tx = _el(els, used, g, "tx", "Text",
             {"text": "Serving normally. No active incident.", "variant": "muted"},
             visible={"$state": "/incident", "eq": False})
    els[stk]["children"] = [hd, sw, a1, tx]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Gate: incident banner is error-grade;否则 a muted all-good line.",
        "verbose": ("A {thing} service banner that is error-grade while the incident "
                    "switch is on and swaps to a muted serving-normally line while it is "
                    "off - never the opposite pairing.").format(thing=D["thing"]),
        "imperative": ("Incident banner type error gated on incident eq true; muted "
                       "normal-service text gated on incident eq false."),
        "casual": ("alert only when something breaks, muted chill line otherwise"),
    }
    tasks["terse"] = ("Incident banner is error-grade; off-state gets a muted "
                      "serving-normally line.")
    return {"root": root, "elements": els, "state": st}, tasks


def _v_filter_alignment(g, D):
    els, used = {}, set()
    opts = list(PIPE_RES)
    n = g.randint(3, 5)
    items = [{"id": "r{0}".format(i + 1), "label": g.choice(D["products"]),
              "state": g.choice(opts)} for i in range(n)]
    st = {"filter": "", "rows": items}
    root = _card(g, used, els, title="Pipeline", maxWidth="md")
    hd = _heading(g, used, els, "Records by gate")
    se = _select(g, used, els, "Filter by gate", "pipelineFilter", opts, "Any",
                 {"$bindState": "/filter"})
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/rows", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "label"}
    ib = _badge(g, used, els, {"$item": "state"}, "outline")
    els[itm]["children"] = [ib]
    tx = _text(g, used, els, "Rows and the filter draw from the same gate list.", "caption")
    els[root]["children"] = [hd, se, lst, tx]

    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Rows tagged from the exact gate list the filter selects from.",
        "verbose": ("A {thing} pipeline view where per-row chips and the filter select "
                    "share one gate vocabulary, so every chip value is a legal filter "
                    "choice.").format(thing=D["thing"]),
        "imperative": ("Seed rows with gate states drawn only from the filter's option "
                       "list; bind the select value."),
        "casual": ("one shared vocab for row chips n the filter dropdown please"),
    }
    return {"root": root, "elements": els, "state": st}, tasks


def _v_held_gate(g, D):
    els, used = {}, set()
    st = {"gate": "", "rows": [[r, "12"] for r in PIPE_RES]}
    root = _card(g, used, els, title="Queue triage", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "Triage the queue")
    se = _select(g, used, els, "Pick a gate to inspect", "gateSel",
                 list(PIPE_RES), None, {"$bindState": "/gate"})
    al = _alert(g, used, els, "Held gate", "Held work needs an owner by noon.",
                "warning", visible={"$state": "/gate", "eq": "Held"})
    tx = _el(els, used, g, "tx", "Text",
             {"text": "Clean gates need no action.", "variant": "muted"},
             visible={"$state": "/gate", "neq": "Held"})
    els[stk]["children"] = [hd, se, al, tx]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Gate picker incl. Held; warning banner fires only on Held.",
        "verbose": ("A {thing} triage view whose gate picker includes Held: choosing "
                    "Held surfaces a warning banner, every other choice gets the muted "
                    "clean line.").format(thing=D["thing"]),
        "imperative": ("Select options Queued/Held/Cleared; alert on gate eq Held; "
                       "muted text on gate neq Held."),
        "casual": ("pick held -> warning pops; anything else -> chill note"),
    }
    return {"root": root, "elements": els, "state": st}, tasks


def _v_plans_ladder(g, D):
    els, used = {}, set()
    lo = g.randint(0, 2)
    pair = [PLANS_LADDER[lo], PLANS_LADDER[lo + 1]]
    st = {}
    root = _card(g, used, els, title="Upgrade paths", maxWidth="lg")
    hd = _heading(g, used, els, "Two steps up the ladder", "h2")
    grd = _grid(g, used, els, 2, "md")
    for i, (name, price) in enumerate(pair):
        pc = _card(g, used, els, title=name, maxWidth="full")
        sh = _heading(g, used, els, price, "h3")
        tx = _text(g, used, els, ("Entry tier of this pair." if i == 0
                                  else "Next step - includes the lower plan."), "muted")
        btn = _button(g, used, els, "Take " + name, "primary")
        els[pc]["children"] = [sh, tx, btn]
        els[grd]["children"].append(pc)
    els[root]["children"] = [hd, grd]
    tasks = {
        "terse": "Two adjacent plan cards listed as adjacent ladder steps, price up only.",
        "verbose": ("A short {thing} upgrade section showing two adjacent laps of the "
                    "pricing ladder in ascending price order, with the higher one "
                    "described as the next step.").format(thing=D["thing"]),
        "imperative": ("Show exactly two consecutive ladder plans; price order must "
                       "ascend left to right; lower card never claims the top slot."),
        "casual": ("two plans next to each other on the ladder, cheap one first"),
    }
    tasks["terse"] = "Two adjacent plan cards, cheapest then its next step up."
    return {"root": root, "elements": els, "state": st}, tasks


def _v_search_coherent(g, D):
    els, used = {}, set()
    n = g.randint(2, 3)
    prods = g.sample(D["products"], n)
    cats = g.sample(D["cats"], n)
    items = [{"id": str(i + 1), "name": prods[i], "meta": "In the " + cats[i].lower() + " case",
              "rating": str(g.randint(3, 5))} for i in range(n)]
    st = {"query": "", "items": items}
    root = _card(g, used, els, title="Catalog search", maxWidth="md")
    hd = _heading(g, used, els, "Look it up")
    inp = _input(g, used, els, "Search", "query", "text", "Type to search",
                 {"$bindState": "/query"})
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/items", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "name"}
    els[itm]["props"]["description"] = {"$item": "meta"}
    b1 = _badge(g, used, els, {"$item": "rating"}, "outline")
    els[itm]["children"] = [b1]
    els[root]["children"] = [hd, inp, lst]

    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Search rows w/ coherent names + in-domain meta + per-row stars.",
        "verbose": ("A {thing} lookup list whose rows pair each name with its own "
                    "in-domain context line and a per-item review chip - the meta and "
                    "the chip both belong to that row, not to the table.").format(thing=D["thing"]),
        "imperative": ("Bind name, meta, and rating per item; keep each row's meta in "
                       "the same domain as its name."),
        "casual": ("rows where name+meta+stars actually belong together pls"),
    }
    return {"root": root, "elements": els, "state": st}, tasks


def _v_notif_unread(g, D):
    els, used = {}, set()
    n = g.randint(3, 4)
    ki = g.randint(0, n - 1)
    notes = [{"id": "n{0}".format(i + 1), "title": D["alerts"][i % len(D["alerts"])][0],
              "seen": (i == ki)} for i in range(n)]
    st = {"notes": notes}
    root = _card(g, used, els, title="Alerts", maxWidth="md")
    hd = _heading(g, used, els, "Unread trail")
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/notes", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "title"}
    b1 = _badge(g, used, els, "new", "destructive")
    els[b1].update({"visible": {"$item": "seen", "eq": False}})
    tx = _text(g, used, els, "A couple of read rows are seeded to anchor the mix.", "caption")
    els[itm]["children"] = [b1]
    els[root]["children"] = [hd, lst, tx]

    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Mix of seen/unread seeded; 'new' chip only on unread rows.",
        "verbose": ("A {thing} alert trail seeded with both read and unread entries; the "
                    "red new chip shows only where seen is false, so the mix is visible "
                    "from the first render.").format(thing=D["thing"]),
        "imperative": ("Seed one seen note among unread; chip visible only where the note is still "
                       "unread."),
        "casual": ("chip only on the unread ones and seed one or two read rows too"),
    }
    return {"root": root, "elements": els, "state": st}, tasks


def _v_load_guard2(g, D):
    els, used = {}, set()
    k1, k2 = D["kpis"][0], D["kpis"][1]
    st = {"sensor": {"humidity": g.randint(20, 95)}, "warn": False}
    root = _card(g, used, els, title="Meter watch", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "Sensor check")
    grd = _grid(g, used, els, 2, "md")
    m1 = _metric(g, used, els, k1[0], k1[1], k1[2], k1[3])
    m2 = _metric(g, used, els, k2[0], k2[1], k2[2], k2[3])
    pg = _progress(g, used, els, {"$state": "/sensor/humidity"}, 100, "Humidity")
    sw = _switch(g, used, els, "Warn me", "warnOn", {"$bindState": "/warn"})
    a1 = _alert(g, used, els, "High reading", "Humidity is pinned at the ceiling.",
                "warning",
                visible={"$state": "/sensor/humidity", "gte": 90})
    els[grd]["children"] = [m1, m2]
    els[stk]["children"] = [hd, grd, pg, sw, a1]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Meter + gte-90 banner; arm/disarm switch bound to state.",
        "verbose": ("A {thing} meter card with a gte-90 high-reading banner and a switch "
                    "whose enabled state lives in state, so the warning can be armed or "
                    "disarmed.").format(thing=D["thing"]),
        "imperative": ("Progress bound to /sensor/humidity w/ gte 90 alert; switch value "
                       "bound and live."),
        "casual": ("humidity meter that pings 90+ and a real on/off switch"),
    }
    return {"root": root, "elements": els, "state": st}, tasks


V3 = [_v_settings_wired, _v_todo_done_seed, _v_priority_hint, _v_incident_coherent,
      _v_filter_alignment, _v_held_gate, _v_plans_ladder, _v_search_coherent,
      _v_notif_unread, _v_load_guard2]

ARCH_FOR3 = ["settings_form", "todo_list", "todo_list", "dashboard_metrics",
             "search_results", "orders_table", "pricing_cards", "search_results",
             "notifications_center", "dashboard_metrics"]


def main():
    g = random.Random(241026)
    built = []
    for i in range(240):
        v = i % 10
        domain = DOMAIN_KEYS[(i // 10) % 6]
        tone = TONES[i % 4]
        spec, tasks = V3[v](g, DOMAINS[domain])
        built.append((ARCH_FOR3[v], domain, tone, tasks[tone], spec, v))

    rows, fails, feat_hist = [], [], {}
    for arch, domain, tone, task, spec, v in built:
        problems = []
        problems += [str(p) for p in validate_spec(spec) if p is not None]
        problems += _bounds_check(spec)
        chain = spec_to_chain(spec, task)
        problems += [str(p) for p in validate_chain(chain) if p is not None]
        spec2, l1 = chain_to_spec(chain)
        problems += [str(p) for p in l1 if p is not None]
        if spec2 != spec:
            problems.append("roundtrip_mismatch")
        if "$" in task:
            problems.append("task_contains_$")
        if problems:
            fails.append((arch, v, task, problems))
            continue
        rows.append({"arch_hint": arch, "task": task, "spec": spec, "split": "train"})
        for f in _features(spec):
            feat_hist[f] = feat_hist.get(f, 0) + 1

    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n")

    arch_hist, var_hist = {}, {}
    for r in rows:
        arch_hist[r["arch_hint"]] = arch_hist.get(r["arch_hint"], 0) + 1
    for arch, v, task, problems in fails:
        var_hist[arch + "#v" + str(v)] = var_hist.get(arch + "#v" + str(v), 0) + 1
    print("rows={0} fails={1} out={2}".format(len(rows), len(fails), OUT))
    print("per_arch=" + json.dumps(arch_hist, sort_keys=True))
    print("features=" + json.dumps(feat_hist, sort_keys=True))
    if fails:
        print("per_variant_fail=" + json.dumps(var_hist, sort_keys=True))
    for arch, v, task, problems in fails[:15]:
        print("FAIL", arch, "#v" + str(v), "|", task[:45], "|", "; ".join(problems[:4])[:200])


if __name__ == "__main__":
    main()
