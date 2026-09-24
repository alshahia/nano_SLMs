"""Batch 002 - PROMPT C hard mode for the U-line prompt kit.

Exercises (per kit PROMPT C): composed NESTED state (2-3 levels), conditional
branches (visible eq/neq/gt/gte on nested paths), lists-of-lists (orders with
per-order line tables via $item), and combined first-draft task texts
("...and add X" in one prompt).

Deliberate exclusions (chain-codec limits, documented in ui/src/chain.py):
- $template interpolation and actions with onSuccess/navigate are NOT
  chain-representable -> skipped (validator/roundtrip gate would fail);
- $template single-token workarounds would train the model on a degenerate
  idiom, so none are emitted.

Output: ui/data/omen_alpha/side_omen_alpha_batch002_hard.jsonl
Same row contract and gate as batch 001.
"""

from __future__ import annotations

import json
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scratch"))
sys.path.insert(0, ROOT)

from omen_side_build import (DOMAINS, DOMAIN_KEYS, TONES, _k, _opt, _el, _card,
                             _stack, _grid, _heading, _text, _badge, _button,
                             _metric, _input, _select, _switch, _progress,
                             _alert, _graph, _table, _series_state,
                             _bounds_check, _features)
from ui.src.validate import validate_spec, validate_chain
from ui.src.chain import spec_to_chain, chain_to_spec

OUT_DIR = os.path.join(ROOT, "ui", "data", "omen_alpha")
OUT = os.path.join(OUT_DIR, "side_omen_alpha_batch002_hard.jsonl")
TONES = ["terse", "verbose", "imperative", "casual"]


# ---------------------------------------------------------- hard variants

def _h_settings_nested(g, D):
    els, used = {}, set()
    p = g.choice(D["people"])
    n = p.split()[-1].lower()
    state = {"profile": {"name": p, "email": n + "@" + D["cats"][0].lower() + ".io"},
             "prefs": {"digest": "weekly", "alertsOn": True}}
    root = _card(g, used, els, title="Account", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    ni = _input(g, used, els, "Full name", "name", "text", None,
                {"$bindState": "/profile/name"},
                [{"type": "required", "message": "Name is required"}])
    ei = _input(g, used, els, "Email", "email", "email", None,
                {"$bindState": "/profile/email"})
    se = _select(g, used, els, "Digest", "digest", ["daily", "weekly", "monthly"],
                 None, {"$bindState": "/prefs/digest"})
    sw = _switch(g, used, els, "Alerts on", "alertsOn", {"$bindState": "/prefs/alertsOn"})
    sv = _button(g, used, els, "Save", "primary", "save_form", {})
    els[stk]["children"] = [ni, ei, se, sw, sv]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Account page w/ nested profile (name/email) + prefs (digest, alerts).",
        "verbose": ("Account settings where identity fields live under a profile group - "
                    "name and email bound into /profile - and the toggles live under "
                    "preferences: digest frequency plus an alerts switch, one Save "
                    "button."),
        "imperative": ("Create settings with two bound sections: profile/name and "
                       "profile/email inputs, a prefs/digest select, a prefs/alertsOn "
                       "switch, and a save action."),
        "casual": ("form with the name/email in profile group n toggles in prefs group "
                   "pls"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _h_dash_nested(g, D):
    els, used = {}, set()
    k1, k2 = D["kpis"][0], D["kpis"][1]
    state = {"kpis": {"primary": {"value": k1[1], "change": k1[2], "trend": k1[3]},
                      "secondary": {"value": k2[1], "change": k2[2], "trend": k2[3]}},
             "trend": {"points": _series_state(D), "title": D["series_title"]}}
    root = _card(g, used, els, title=D["dash_title"], maxWidth="lg")
    stk = _stack(g, used, els, "vertical", "lg")
    hd = _heading(g, used, els, D["dash_title"], "h2")
    grd = _grid(g, used, els, 2, "md")
    m1 = _metric(g, used, els, k1[0], {"$state": "/kpis/primary/value"},
                 {"$state": "/kpis/primary/change"}, {"$state": "/kpis/primary/trend"})
    m2 = _metric(g, used, els, k2[0], {"$state": "/kpis/secondary/value"},
                 {"$state": "/kpis/secondary/change"}, {"$state": "/kpis/secondary/trend"})
    cht = _graph(g, used, els, {"$state": "/trend/points"},
                 {"$state": "/trend/title"})
    els[grd]["children"] = [m1, m2]
    els[stk]["children"] = [hd, grd, cht]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "KPI pair + chart, everything nested under kpis/ and trend/ in state.",
        "verbose": ("Overview screen for {thing} where the numbers - {m1}, {m2} - read "
                    "from a nested kpis object and the chart reads its points and title "
                    "from a trend object.").format(thing=D["thing"], m1=k1[0], m2=k2[0]),
        "imperative": ("Compose a dashboard whose state is nested: kpis.primary, "
                       "kpis.secondary (value/change/trend each) and trend.points; bind "
                       "two metrics and one chart to those paths."),
        "casual": ("dashboard using nested state (kpis.x / trend.points) instead of flat "
                   "keys ty"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _h_orders_lines(g, D):
    els, used = {}, set()
    n = g.randint(2, 3)
    orders = []
    for i in range(n):
        lines = [[g.choice(D["products"]), str(g.randint(1, 4)),
                  "$" + str(g.randint(9, 90))] for _ in range(g.randint(2, 3))]
        orders.append({"id": str(5000 + i), "customer": g.choice(D["people"]),
                       "status": g.choice(D["statuses"]), "lines": lines})
    state = {"orders": orders}
    root = _card(g, used, els, title="Orders detail", maxWidth="lg")
    hd = _heading(g, used, els, "Orders with line items")
    lst = _stack(g, used, els, "vertical", "md",
                 repeat={"statePath": "/orders", "key": "id"})
    itm = _card(g, used, els, title={"$item": "customer"}, maxWidth="full")
    els[itm]["props"]["description"] = None
    bd = _badge(g, used, els, {"$item": "status"}, "outline")
    tbl = _table(g, used, els, ["SKU", "Qty", "Price"], {"$item": "lines"})
    els[itm]["children"] = [bd, tbl]
    tx = _text(g, used, els, "Each card lists that order's line items.", "caption")
    els[root]["children"] = [hd, lst, tx]
    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Orders expanded as cards; each embeds its own line-item table.",
        "verbose": ("Order cards instead of one big table: repeat over the orders and "
                    "give every card the customer name, a status chip, and its own line- "
                    "item table (SKU, qty, price) straight off the item."),
        "imperative": ("Render orders as repeated cards, each embedding a Table whose "
                       "rows bind to that item's lines field (list of lists)."),
        "casual": ("order cards w/ the line items as a mini table inside each one pls"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _h_orders_flags(g, D):
    els, used = {}, set()
    cols = ["Order", "Customer", "Total", "Status"]
    rows = [[str(6000 + i), p, "$" + str(g.randint(15, 480)), g.choice(D["statuses"])]
            for i, p in enumerate(g.sample(D["people"], g.randint(3, 5)))]
    state = {"flags": {"held": False, "rush": False}, "cols": cols, "rows": rows}
    root = _card(g, used, els, title="Queue health", maxWidth="lg")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "Review the queue")
    tbl = _table(g, used, els, {"$state": "/cols"}, {"$state": "/rows"})
    a1 = _alert(g, used, els, "Held orders", "Held orders need review before end of day.",
                "warning", visible={"$state": "/flags/held", "eq": True})
    a2 = _alert(g, used, els, "Rush window", "Rush orders are past their promised time.",
                "error", visible={"$state": "/flags/rush", "eq": True})
    a3 = _alert(g, used, els, "All clear", "No flags active on the queue.", "success",
                visible={"$state": "/flags/held", "neq": True})
    brow = _stack(g, used, els, "horizontal", "sm")
    b1 = _button(g, used, els, "Rescan flags", "secondary", "refresh_data", {})
    els[brow]["children"] = [b1]
    els[stk]["children"] = [hd, tbl, a1, a2, a3]
    els[root]["children"] = [stk, brow]
    tasks = {
        "terse": "Orders + 3 gating alerts on flags.held / flags.rush (else all-clear).",
        "verbose": ("A queue view over a nested flags object: held and rush banners only "
                    "when their flag is true, an all-clear otherwise, above a state-"
                    "driven table.",
                    ),
        "imperative": ("Build nested-flag alerts: warning on flags/held eq true, another "
                       "on flags/rush eq true, success note on held neq true."),
        "casual": ("queue w/ nested flag banners - held n rush pop only when set"),
    }
    tasks["verbose"] = ("A queue view over a nested flags object: held and rush banners "
                        "whenever their flag is true, an all-clear success note "
                        "otherwise, above the state-driven orders table.")
    return {"root": root, "elements": els, "state": state}, tasks


def _h_pricing_billing(g, D):
    els, used = {}, set()
    names = g.sample(PLANS := ["Starter", "Pro", "Team"], 2)
    state = {"billing": "monthly"}
    root = _card(g, used, els, title="Billing", maxWidth="lg")
    hd = _heading(g, used, els, "Pick a cycle first", "h2")
    tg = _el(els, used, g, "tg", "ToggleGroup",
             {"items": [{"label": "Monthly", "value": "monthly"},
                        {"label": "Yearly (2 months free)", "value": "yearly"}],
              "type": "single", "value": "monthly"}, children=[])
    grd = _grid(g, used, els, 2, "md")
    for i, name in enumerate(names):
        pc = _card(g, used, els, title=name, maxWidth="full")
        hd2 = _heading(g, used, els, PRICES[i], "h3")
        txm = _text(g, used, els, PRICES[i], "lead")
        txy = _text(g, used, els,
                    "$" + PRICES[i].split("$")[1].split("/")[0] + "0/yr", "lead")
        topm = {"visible": {"$state": "/billing", "eq": "monthly"}}
        topy = {"visible": {"$state": "/billing", "neq": "monthly"}}
        els[txm].update(topm)
        els[txy].update(topy)
        btn = _button(g, used, els, "Choose " + name, "primary")
        els[pc]["children"] = [hd2, txm, txy, btn]
        els[grd]["children"].append(pc)
    els[root]["children"] = [hd, tg, grd]
    tasks = {
        "terse": "Two plans; price text swaps monthly/yearly off the billing toggle.",
        "verbose": ("A plan section where the toggle (monthly/yearly) drives which price "
                    "text shows: the monthly price hidden in yearly mode and vice versa."),
        "imperative": ("Bind plans to a billing toggle using two visible branches per "
                       "card: eq monthly and neq monthly swap the price text."),
        "casual": ("billing toggle switches the price text on each card plz"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _h_search_empty(g, D):
    els, used = {}, set()
    n = g.randint(2, 3)
    results = [{"id": str(i + 1), "name": p,
                "meta": g.choice(D["cats"])} for i, p in enumerate(g.sample(D["products"], n))]
    state = {"query": "", "page": 1, "empty": False, "results": results}
    root = _card(g, used, els, title="Search", maxWidth="md")
    hd = _heading(g, used, els, "Find records")
    inp = _input(g, used, els, "Search", "query", "text", "Type to search...",
                 {"$bindState": "/query"})
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/results", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "name"}
    els[itm]["props"]["description"] = {"$item": "meta"}
    empty = _el(els, used, g, "em", "Text",
                {"text": "No matches yet - try another term.", "variant": "muted"},
                visible={"$state": "/empty", "eq": True})
    pg = _el(els, used, g, "pg", "Pagination",
             {"totalPages": g.randint(3, 9), "page": {"$bindState": "/page"}},
             children=[], on={"change": {"action": "load_data", "params": {}}})
    els[root]["children"] = [hd, inp, lst, empty, pg]
    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Search list + pager + empty note on the empty flag.",
        "verbose": ("A search panel that also handles nothing-found: when the empty flag "
                    "flips, the muted no-matches note takes over while the results list "
                    "stays quiet."),
        "imperative": ("Create a repeat-backed search list and an empty-state text gated "
                       "on a boolean state flag, plus pagination that loads data."),
        "casual": ("results list w/ a friendly 'no matches' fallback when empty, thx"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _h_notif_nested(g, D):
    els, used = {}, set()
    n = g.randint(3, 4)
    kinds = ["info", "warning", "error", "success"]
    notes = [{"id": "n{0}".format(i + 1),
              "title": D["alerts"][i % len(D["alerts"])][0],
              "kind": g.choice(kinds)} for i in range(n)]
    state = {"inbox": {"unread": g.randint(5, 30), "items": notes}}
    root = _card(g, used, els, title="Inbox", maxWidth="md")
    hd = _heading(g, used, els, "Notifications")
    bd = _badge(g, used, els, {"$state": "/inbox/unread"}, "destructive")
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/inbox/items", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "title"}
    kb = _badge(g, used, els, {"$item": "kind"}, "outline")
    warn = _alert(g, used, els, "Unread piling up",
                  "Over 10 unread - consider a bulk clear.",
                  "warning",
                  visible={"$state": "/inbox/unread", "gte": 10})
    btn = _button(g, used, els, "Mark all read", "secondary", "setState",
                  {"statePath": "/inbox/unread", "value": 0})
    els[itm]["children"] = [kb]
    els[root]["children"] = [hd, bd, warn, lst, btn]
    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Inbox nested under inbox/ - unread badge, gte-10 warning, list, clear.",
        "verbose": ("An inbox whose state nests unread count and items under inbox/: a "
                    "red unread badge, a warning banner once unread is 10+, the item "
                    "list with kind chips, and mark-all-read."),
        "imperative": ("Bind to nested inbox state: unread badge on /inbox/unread, items "
                       "repeat on /inbox/items, a gte threshold alert, and a bulk clear "
                       "action."),
        "casual": ("notif inbox w/ nested unread counter - banner at 10+, chips on "
                   "rows, big clear btn"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _h_profile_deep(g, D):
    els, used = {}, set()
    person = g.choice(D["people"])
    pct = g.randint(40, 95)
    rat = g.randint(3, 5)
    state = {"person": {"name": person,
                        "blurb": "Runs the " + g.choice(D["cats"]).lower() + " desk.",
                        "skills": {"primary": g.choice(D["cats"]),
                                   "secondary": g.choice(D["cats"])},
                        "stats": {"rating": rat, "completion": pct}}}
    root = _card(g, used, els, maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md", align="center")
    av = _el(els, used, g, "av", "Avatar",
             {"name": {"$state": "/person/name"}, "size": "lg"}, children=[])
    hd = _heading(g, used, els, {"$state": "/person/name"}, "h2")
    tx = _text(g, used, els, {"$state": "/person/blurb"}, "muted")
    brow = _stack(g, used, els, "horizontal", "sm")
    b1 = _badge(g, used, els, {"$state": "/person/skills/primary"}, "default")
    b2 = _badge(g, used, els, {"$state": "/person/skills/secondary"}, "outline")
    pg = _progress(g, used, els, {"$state": "/person/stats/completion"}, 100,
                   "Profile completeness")
    els[brow]["children"] = [b1, b2]
    els[stk]["children"] = [av, hd, tx, brow, pg]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Profile fully bound to a nested person/ object (name, blurb, skills, stats).",
        "verbose": ("One profile card whose state is a person object: name drives both "
                    "the avatar label and heading, blurb the sub-line, skills primary/"
                    "secondary the chips, and stats.completion the meter."),
        "imperative": ("Bind every profile element into nested paths: /person/name, "
                       "/person/blurb, /person/skills/*, /person/stats/completion."),
        "casual": ("profile card reading ALL its bits from one nested person object"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _h_todo_nested_draft(g, D):
    els, used = {}, set()
    n = g.randint(2, 4)
    items = [{"id": "t{0}".format(i + 1), "title": g.choice(D["tasks"]),
              "priority": g.choice(PRIORITIES), "done": g.random() < 0.3}
             for i in range(n)]
    state = {"draft": {"title": "", "priority": "Medium"}, "items": items}
    root = _card(g, used, els, title="Quick add board", maxWidth="md")
    nw = _input(g, used, els, "New task", "draftTitle", "text", "What needs doing?",
                {"$bindState": "/draft/title"})
    se = _select(g, used, els, "Priority", "draftPriority", PRIORITIES, None,
                 {"$bindState": "/draft/priority"})
    ad = _button(g, used, els, "Add task", "primary", "pushState",
                 {"statePath": "/items", "value": {"$state": "/draft/title"},
                  "title": {"$state": "/draft/title"},
                  "priority": {"$state": "/draft/priority"},
                  "done": False, "id": "$id"})
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/items", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "title"}
    bd = _badge(g, used, els, {"$item": "priority"}, "outline")
    els[itm]["children"] = [bd]
    els[root]["children"] = [nw, se, ad, lst]
    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Task capture: draft.title + draft.priority nest in state; add pushes out.",
        "verbose": ("A quick-add task board where the pending title and chosen priority "
                    "live under a draft object in state; the Add button pushes a "
                    "structured item into the list and rows carry priority chips."),
        "imperative": ("Bind the input and select to draft/title and draft/priority, then "
                       "push both into items on add; badge each row by priority."),
        "casual": ("task adder where the unsent draft lives in a lil draft object n add "
                   "spawns from it"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _h_dash_thresholds(g, D):
    els, used = {}, set()
    k1, k2 = D["kpis"][0], D["kpis"][1]
    cpu = g.randint(30, 95)
    state = {"caps": {"cpu": cpu, "mem": g.randint(30, 90)}, "ok": cpu < 90}
    root = _card(g, used, els, title="Load guard", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "Load watch")
    grd = _grid(g, used, els, 2, "md")
    m1 = _metric(g, used, els, k1[0], k1[1], k1[2], k1[3])
    m2 = _metric(g, used, els, k2[0], k2[1], k2[2], k2[3])
    pg = _progress(g, used, els, {"$state": "/caps/cpu"}, 100, "CPU load")
    a1 = _alert(g, used, els, "Approaching saturation", "CPU load is 90% or higher.",
                "error", visible={"$state": "/caps/cpu", "gte": 90})
    a2 = _alert(g, used, els, "Nominal", "All load signals nominal.", "success",
                visible={"$state": "/ok", "eq": True})
    els[grd]["children"] = [m1, m2]
    els[stk]["children"] = [hd, grd, pg, a1, a2]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Load view: CPU bar w/ 90%+ error alert; nested caps in state.",
        "verbose": ("A load guard for {thing}: the two reference numbers, a CPU bar "
                    "reading off a nested caps object, and a saturation banner that fires "
                    "only at 90% or more.").format(thing=D["thing"]),
        "imperative": ("Bind progress to /caps/cpu and gate an error alert on gte 90; "
                       "keep both reference metrics in a two-column row."),
        "casual": ("cpu bar that yells at 90%+ n otherwise chills, nested state plz"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


HARD_VARIANTS = [
    _h_settings_nested, _h_dash_nested, _h_orders_lines, _h_orders_flags,
    _h_pricing_billing, _h_search_empty, _h_notif_nested, _h_profile_deep,
    _h_todo_nested_draft, _h_dash_thresholds,
]

ARCH_FOR = [
    "settings_form", "dashboard_metrics", "orders_table", "orders_table",
    "pricing_cards", "search_results", "notifications_center", "profile_card",
    "todo_list", "dashboard_metrics",
]

PLANS2 = ["Starter", "Pro", "Team"]
PRICES = ["$9/mo", "$19/mo", "$49/mo", "$99/mo", "$199/mo"]
PRIORITIES = ["Low", "Medium", "High"]


def main():
    import random
    g = random.Random(241012)
    built = []
    for i in range(240):
        v = i % 10
        domain = DOMAIN_KEYS[(i // 10) % 6]
        tone = TONES[i % 4]
        D = DOMAINS[domain]
        spec, tasks = HARD_VARIANTS[v](g, D)
        built.append((ARCH_FOR[v], domain, tone, tasks[tone], spec, v))

    rows, fails = [], []
    feat_hist = {}
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
        print("FAIL", arch, "#v" + str(v), "|", task[:50], "|", "; ".join(problems[:4])[:220])


if __name__ == "__main__":
    main()
