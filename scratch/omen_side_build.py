"""Build the first LLM-authored side-data batch for the U-line prompt kit
(ui/prompts/DATA_GEN_PROMPTS.md, PROMPT A/B contract).

Output : ui/data/omen_alpha/side_omen_alpha_batch001.jsonl
Rows   : {"arch_hint", "task", "spec", "split": "train"}
Gate   : every row must pass validate_chain(spec_to_chain(spec, task)) with
         zero issues, plus a full spec->chain->spec round-trip equality check
         and the structural budget (6..16 elements, depth<=4, siblings<=5).

Authorship note: hand-designed structural templates (34 variants across the 8
archetypes) parametrized by 6 domains x 4 task tones x feature flags; sampled
with a fixed seed for reproducibility.

Usage (venv, repo root):
    python scratch/omen_side_build.py
"""

from __future__ import annotations

import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.src.chain import spec_to_chain, chain_to_spec
from ui.src.validate import validate_chain, validate_spec

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "ui", "data", "omen_alpha")
OUT = os.path.join(OUT_DIR, "side_omen_alpha_batch001.jsonl")

TONES = ["terse", "verbose", "imperative", "casual"]

# ---------------------------------------------------------------- domain banks

DOMAINS = {
    "retail": {
        "people": ["Ava Thompson", "Noah Patel", "Mia Chen", "Liam O'Brien",
                   "Zoe Ramirez", "Ethan Brooks"],
        "products": ["Trail running shoes", "Ceramic pour-over kit",
                     "Linen throw pillow", "Steel water bottle",
                     "Bluetooth speaker", "Wool beanie", "Canvas tote",
                     "Desk organizer"],
        "tasks": ["Restock bestsellers", "Call the supplier",
                  "Print shipping labels", "Refresh homepage banners",
                  "Audit promo codes", "Photograph new arrivals"],
        "kpis": [("Revenue", "$48,210", "+12.4%", "1"),
                 ("Orders", "1,284", "-3.1%", "-1"),
                 ("Avg basket", "$37.60", "+1.2%", "1"),
                 ("Returns", "42", "0", "0"),
                 ("Conversion", "3.9%", "+0.4%", "1"),
                 ("Refunds", "$812", "-8%", "-1")],
        "statuses": ["Paid", "Pending", "Shipped", "Refunded"],
        "cats": ["Apparel", "Home", "Electronics", "Outdoor"],
        "series": [("Q1", "$310k"), ("Q2", "$348k"), ("Q3", "$402k"), ("Q4", "$467k")],
        "series_label": "quarterly sales",
        "series_title": "Sales by quarter",
        "thing": "the store",
        "dash_title": "Store overview",
        "alerts": [("Low stock", "3 items are below the reorder point.", "warning"),
                   ("Order delivered", "Order #1042 was delivered today.", "success"),
                   ("Payment failed", "A card charge was declined.", "error"),
                   ("Weekend sale", "The weekend sale starts Friday.", "info")],
        "roles": ["Cashier", "Shift lead", "Manager"],
    },
    "healthcare": {
        "people": ["Dr. Amara Osei", "Dana Whitfield", "Dr. Felix Grant",
                   "Rosa Delgado", "Dr. Hana Ito", "Marcus Bell"],
        "products": ["Patient intake form", "Lab results portal",
                     "Refill request queue", "Discharge checklist",
                     "Follow-up scheduler", "Vitals tracker"],
        "tasks": ["Review lab results", "Prep patient intake",
                  "Approve a medication refill", "Finish discharge paperwork",
                  "Schedule follow-ups", "Restock exam room 2"],
        "kpis": [("Appointments", "312", "+4%", "1"),
                 ("Bed occupancy", "78%", "+2%", "1"),
                 ("Avg wait", "18 min", "-5 min", "-1"),
                 ("No-shows", "23", "+6", "-1"),
                 ("Discharges", "88", "+3", "1"),
                 ("Readmissions", "11", "-2", "-1")],
        "statuses": ["Scheduled", "Admitted", "Discharged", "Critical"],
        "cats": ["Cardiology", "Pediatrics", "Radiology", "General"],
        "series": [("Mon", 42), ("Tue", 51), ("Wed", 47), ("Thu", 58), ("Fri", 39)],
        "series_label": "weekly appointments",
        "series_title": "Appointments by day",
        "thing": "the clinic",
        "dash_title": "Clinic pulse",
        "alerts": [("Lab results ready", "3 results are awaiting review.", "info"),
                   ("Critical vitals", "Room 4 flagged critical vitals.", "error"),
                   ("Shift change", "Night shift handoff at 19:00.", "info"),
                   ("Vaccine stock", "Flu vaccine stock is low.", "warning")],
        "roles": ["Nurse", "Physician", "Admin"],
    },
    "education": {
        "people": ["Karen Whitmore", "Sam Alvarez", "Dr. Iris Novak",
                   "Toby Marshall", "Lena Fischer", "Omar Haddad"],
        "products": ["Quiz portal", "Lesson planner", "Gradebook",
                     "Attendance tracker", "Parent messenger", "Reading list"],
        "tasks": ["Grade the quizzes", "Prep the week 6 lesson",
                  "Email the parents", "Update the syllabus",
                  "Book the computer lab", "Review project drafts"],
        "kpis": [("Enrollment", "1,432", "+38", "1"),
                 ("Attendance", "94%", "-1%", "-1"),
                 ("Avg score", "82.5", "+2.1", "1"),
                 ("Missing work", "57", "-12", "-1"),
                 ("Active courses", "24", "0", "0"),
                 ("Grad rate", "91%", "+0.6%", "1")],
        "statuses": ["Enrolled", "Active", "On leave", "Graduated"],
        "cats": ["Math", "Science", "History", "Art"],
        "series": [("Unit 1", 74), ("Unit 2", 78), ("Unit 3", 81), ("Unit 4", 85)],
        "series_label": "scores by unit",
        "series_title": "Class average by unit",
        "thing": "the course",
        "dash_title": "Term overview",
        "alerts": [("Grades due", "Midterm grades are due Friday.", "warning"),
                   ("Field trip", "Permission slips are overdue.", "info"),
                   ("System notice", "The gradebook syncs tonight.", "info"),
                   ("Low attendance", "Period 3 attendance dropped.", "error")],
        "roles": ["Student", "Teacher", "Advisor"],
    },
    "logistics": {
        "people": ["Ray Kowalski", "Ines Duarte", "Viktor Petrov",
                   "Nadia Rahman", "Cole Bridges", "Sofia Marino"],
        "products": ["Shipment tracker", "Carrier booking desk",
                     "Route planner", "Customs forms", "Pallet inspector",
                     "ETA board"],
        "tasks": ["Book a carrier", "Update the ETAs", "Inspect pallets",
                  "File customs forms", "Reroute truck 12", "Print manifests"],
        "kpis": [("Shipments", "2,041", "+9%", "1"),
                 ("On-time", "96.2%", "-0.8%", "-1"),
                 ("Fleet use", "87%", "+3%", "1"),
                 ("Delays", "17", "-4", "-1"),
                 ("Damaged", "6", "0", "0"),
                 ("Cost/mile", "$1.84", "-2%", "-1")],
        "statuses": ["In transit", "Delivered", "Held", "Returned"],
        "cats": ["Freight", "Last-mile", "Cold chain", "Air"],
        "series": [("W1", 412), ("W2", 448), ("W3", 471), ("W4", 502)],
        "series_label": "weekly shipments",
        "series_title": "Shipments by week",
        "thing": "the fleet",
        "dash_title": "Fleet overview",
        "alerts": [("Route delay", "Truck 7 is 40 minutes behind.", "warning"),
                   ("Delivered", "Shipment #8812 reached the hub.", "success"),
                   ("Customs hold", "Two pallets are held at customs.", "error"),
                   ("Weather advisory", "Icy roads on the north route.", "info")],
        "roles": ["Dispatcher", "Driver", "Ops manager"],
    },
    "finance": {
        "people": ["Grace Lin", "Hugo Fernandes", "Priya Nair",
                   "Tom Gallagher", "Yusuf Demir", "Clara Voss"],
        "products": ["Ledger view", "Invoice approver", "Expense claims",
                     "Monthly close checklist", "Budget planner", "Audit log"],
        "tasks": ["Reconcile the ledger", "Approve invoices",
                  "Flag duplicates", "Prep the monthly close",
                  "Audit expense claims", "Draft the board summary"],
        "kpis": [("Balance", "$1.24M", "+3.2%", "1"),
                 ("Inflow", "$310k", "+11%", "1"),
                 ("Outflow", "$264k", "-4%", "-1"),
                 ("Overdue", "9", "+2", "-1"),
                 ("Runway", "18 mo", "0", "0"),
                 ("Burn", "$61k", "-5%", "-1")],
        "statuses": ["Cleared", "Pending", "Flagged", "Settled"],
        "cats": ["Payroll", "Vendors", "Travel", "Software"],
        "series": [("Jan", "$182k"), ("Feb", "$204k"), ("Mar", "$231k"), ("Apr", "$262k")],
        "series_label": "monthly cash flow",
        "series_title": "Cash flow by month",
        "thing": "the fund",
        "dash_title": "Portfolio overview",
        "alerts": [("Invoice overdue", "Invoice #2201 is 6 days overdue.", "warning"),
                   ("Close complete", "April close finished cleanly.", "success"),
                   ("Anomaly", "Unusual spend in Software.", "error"),
                   ("Rate change", "Bank fees change next month.", "info")],
        "roles": ["Analyst", "Controller", "Partner"],
    },
    "gaming": {
        "people": ['Kira "Vex" Moon', "Jax Correa", "Elena Frost",
                   "Dante Reyes", "Mika Tanaka", "Ravi Sharma"],
        "products": ["Patch notes page", "Bug triage board", "Event planner",
                     "Leaderboard", "Report queue", "Drop-rate tuner"],
        "tasks": ["Triage bug reports", "Draft the patch notes",
                  "Plan the fall event", "Review player reports",
                  "Tune drop rates", "Schedule the maintenance window"],
        "kpis": [("DAU", "84,120", "+6%", "1"),
                 ("Avg session", "36 min", "+0.2", "1"),
                 ("Revenue", "$52.4k", "+18%", "1"),
                 ("Churn", "4.1%", "-0.3%", "-1"),
                 ("Reports", "212", "-14", "-1"),
                 ("CCU", "12,480", "+410", "1")],
        "statuses": ["Ranked", "Casual", "Banned", "New"],
        "cats": ["FPS", "RPG", "Racing", "Puzzle"],
        "series": [("Patch 1.1", 61), ("Patch 1.2", 66), ("Patch 1.3", 72), ("Patch 1.4", 79)],
        "series_label": "playtime by patch",
        "series_title": "Playtime by patch",
        "thing": "the game",
        "dash_title": "Live ops overview",
        "alerts": [("Server issue", "EU-West is experiencing lag.", "error"),
                   ("Event live", "The fall event is now live.", "success"),
                   ("Maintenance", "Servers restart at 04:00 UTC.", "info"),
                   ("Report spike", "Reports doubled in the last hour.", "warning")],
        "roles": ["Player", "Moderator", "Guild lead"],
    },
}
DOMAIN_KEYS = list(DOMAINS)

PLANS = ["Starter", "Pro", "Team", "Plus", "Solo"]
PRICES = ["$9/mo", "$19/mo", "$49/mo", "$99/mo", "$199/mo"]
FEATURES = ["Unlimited projects", "Priority support", "Advanced analytics",
            "Team seats", "Custom domain", "API access", "SSO login", "Audit log"]
PRIORITIES = ["Low", "Medium", "High"]

# ------------------------------------------------------------------- helpers


def _k(g, prefix, used):
    while True:
        s = prefix + "".join(g.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(3))
        if s not in used:
            used.add(s)
            return s


def _opt(g, props):
    """Optional-prop discipline: keep, drop, or null - never invent."""
    out = {}
    for k, v in props.items():
        if v is not None:
            out[k] = v
        elif g.random() < 0.45:
            out[k] = None
    return out


def _el(els, used, g, prefix, ctype, props, children=None, **top):
    key = _k(g, prefix, used)
    el = {"type": ctype, "props": props, "children": children if children is not None else []}
    for k, v in top.items():
        el[k] = v
    els[key] = el
    return key


def _card(g, used, els, title=None, desc=None, maxWidth=None, centered=None, children=None):
    return _el(els, used, g, "card", "Card",
               _opt(g, {"title": title, "description": desc, "maxWidth": maxWidth,
                        "centered": centered}), children)


def _stack(g, used, els, direction="vertical", gap=None, align=None, justify=None,
           children=None, repeat=None):
    props = {"direction": direction}
    if gap:
        props["gap"] = gap
    elif g.random() < 0.6:
        props["gap"] = g.choice(["sm", "md", "lg"])
    for name, v in (("align", align), ("justify", justify)):
        if v:
            props[name] = v
        elif g.random() < 0.2:
            props[name] = g.choice(["start", "center", "stretch"] if name == "align"
                                    else ["start", "center", "between"])
    top = {"repeat": repeat} if repeat else {}
    return _el(els, used, g, "stk", "Stack", props, children, **top)


def _grid(g, used, els, columns=None, gap=None, children=None):
    props = {}
    if columns:
        props["columns"] = columns
    else:
        props["columns"] = g.randint(1, 3)
    if gap:
        props["gap"] = gap
    return _el(els, used, g, "grd", "Grid", props, children)


def _heading(g, used, els, text, level=None):
    props = {"text": text}
    props["level"] = level or g.choice(["h2", "h2", "h3"])
    return _el(els, used, g, "hd", "Heading", props)


def _text(g, used, els, text, variant=None):
    props = {"text": text}
    if variant:
        props["variant"] = variant
    elif g.random() < 0.5:
        props["variant"] = g.choice(["body", "caption", "muted", "lead"])
    return _el(els, used, g, "tx", "Text", props)


def _badge(g, used, els, text, variant=None, visible=None):
    props = {"text": text}
    props["variant"] = variant or g.choice(["default", "secondary", "outline", "default"])
    top = {"visible": visible} if visible else {}
    return _el(els, used, g, "bd", "Badge", props, **top)


def _button(g, used, els, label, variant=None, action=None, params=None, disabled=None):
    props = {"label": label}
    props["variant"] = variant or g.choice(["primary", "primary", "secondary"])
    if disabled:
        props["disabled"] = disabled
    top = {}
    if action:
        top["on"] = {"press": {"action": action, "params": params or {}}}
    return _el(els, used, g, "btn", "Button", props, **top)


def _metric(g, used, els, label, value, change=None, changeType=None, prefix=None, suffix=None):
    props = {"label": label, "value": value}
    for k, v in (("change", change), ("changeType", changeType),
                 ("prefix", prefix), ("suffix", suffix)):
        if v is not None:
            props[k] = v
        elif k == "change" and g.random() < 0.2:
            props[k] = None
    return _el(els, used, g, "met", "Metric", props)


def _input(g, used, els, label, name, type_="text", placeholder=None, value=None, checks=None):
    props = {"label": label, "name": name, "type": type_}
    if placeholder:
        props["placeholder"] = placeholder
    if value is not None:
        props["value"] = value
    if checks:
        props["checks"] = checks
    return _el(els, used, g, "in", "Input", props)


def _select(g, used, els, label, name, options, placeholder=None, value=None):
    props = {"label": label, "name": name, "options": options}
    if placeholder:
        props["placeholder"] = placeholder
    if value is not None:
        props["value"] = value
    return _el(els, used, g, "sel", "Select", props)


def _switch(g, used, els, label, name, checked=None):
    props = {"label": label, "name": name}
    if checked is not None:
        props["checked"] = checked
    return _el(els, used, g, "sw", "Switch", props)


def _progress(g, used, els, value, max_=None, label=None):
    props = {"value": value}
    if max_:
        props["max"] = max_
    if label:
        props["label"] = label
    return _el(els, used, g, "pg", "Progress", props)


def _alert(g, used, els, title, message, type_=None, visible=None):
    props = {"title": title, "message": message}
    if type_:
        props["type"] = type_
    top = {"visible": visible} if visible else {}
    return _el(els, used, g, "al", "Alert", props, **top)


def _graph(g, used, els, data, title=None):
    ctype = "BarGraph" if g.random() < 0.5 else "LineGraph"
    props = {"data": data}
    if title:
        props["title"] = title
    return _el(els, used, g, "cht", ctype, props)


def _table(g, used, els, columns, rows, caption=None):
    props = {"columns": columns, "rows": rows}
    if caption:
        props["caption"] = caption
    return _el(els, used, g, "tbl", "Table", props)


def _series_state(D):
    return [{"label": a, "value": b} for a, b in D["series"]]


# ------------------------------------------------------------- dashboard variants


def _dash_overview(g, D):
    els, used = {}, set()
    l1, v1, c1, t1 = D["kpis"][0]
    l2, v2, c2, t2 = D["kpis"][1]
    state = {"primary": v1, "primaryChange": c1, "primaryTrend": t1,
             "secondary": v2, "secondaryChange": c2, "secondaryTrend": t2,
             "series": _series_state(D)}
    root = _card(g, used, els, title=D["dash_title"], maxWidth=g.choice(["md", "lg"]))
    stk = _stack(g, used, els, "vertical", g.choice(["md", "lg"]))
    hd = _heading(g, used, els, D["dash_title"])
    grd = _grid(g, used, els, 2, g.choice(["md", "lg"]))
    m1 = _metric(g, used, els, l1, {"$state": "/primary"}, {"$state": "/primaryChange"},
                 {"$state": "/primaryTrend"})
    m2 = _metric(g, used, els, l2, {"$state": "/secondary"}, {"$state": "/secondaryChange"},
                 {"$state": "/secondaryTrend"})
    cht = _graph(g, used, els, {"$state": "/series"}, D["series_title"])
    els[grd]["children"] = [m1, m2]
    els[stk]["children"] = [hd, grd, cht]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "{thing} KPIs: {m1} and {m2}, plus a {sl} chart.".format(
            thing=D["thing"], m1=l1, m2=l2, sl=D["series_label"]),
        "verbose": ("I need a small overview screen for {thing}. Put {m1} and {m2} as "
                    "the two headline numbers, then a {sl} chart underneath so the "
                    "trend is easy to read at a glance.").format(
            thing=D["thing"], m1=l1, m2=l2, sl=D["series_label"]),
        "imperative": ("Build a dashboard for {thing} showing {m1} and {m2} as metrics "
                       "with a {sl} chart below.").format(
            thing=D["thing"], m1=l1, m2=l2, sl=D["series_label"]),
        "casual": ("can u make a quick {thing} dashboard? two big numbers ({m1}, {m2}) "
                   "and a {sl} chart pls").format(
            thing=D["thing"], m1=l1, m2=l2, sl=D["series_label"]),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _dash_table(g, D):
    els, used = {}, set()
    l1, v1, c1, t1 = D["kpis"][0]
    l2, v2, c2, t2 = D["kpis"][1]
    cols = ["Name", "Region", "Total", "Status"]
    rows = [[p, g.choice(["North", "South", "East", "West"]),
             "$" + str(g.randint(20, 900)), g.choice(D["statuses"])]
            for p in g.sample(D["people"], g.randint(3, 5))]
    state = {"primary": v1, "primaryChange": c1, "primaryTrend": t1,
             "secondary": v2, "secondaryChange": c2, "secondaryTrend": t2,
             "cols": cols, "rows": rows}
    root = _card(g, used, els, title=D["dash_title"], maxWidth="lg")
    stk = _stack(g, used, els, "vertical", "lg")
    hd = _heading(g, used, els, "Top performers")
    grd = _grid(g, used, els, 2, "md")
    m1 = _metric(g, used, els, l1, {"$state": "/primary"}, {"$state": "/primaryChange"},
                 {"$state": "/primaryTrend"})
    m2 = _metric(g, used, els, l2, {"$state": "/secondary"}, {"$state": "/secondaryChange"},
                 {"$state": "/secondaryTrend"})
    tbl = _table(g, used, els, {"$state": "/cols"}, {"$state": "/rows"})
    els[grd]["children"] = [m1, m2]
    els[stk]["children"] = [hd, grd, tbl]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "{thing} numbers on top, a {what} breakdown table below.".format(
            thing=D["thing"], what=D["cats"][0].lower()),
        "verbose": ("For {thing} I want two summary numbers at the top - {m1} and {m2} - "
                    "and under them a table breaking the numbers down by person with a "
                    "status column.").format(thing=D["thing"], m1=l1, m2=l2),
        "imperative": ("Create a dashboard: {m1} and {m2} metrics, then a table listing "
                       "each person, their region, total, and status.").format(m1=l1, m2=l2),
        "casual": ("dashboard time :) {m1} + {m2} up top, then a lil table of who did "
                   "what with statuses").format(m1=l1, m2=l2),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _dash_stateless(g, D):
    els, used = {}, set()
    l1, v1, _, _ = D["kpis"][0]
    l2, v2, _, _ = D["kpis"][1]
    status = g.choice(D["statuses"])
    root = _card(g, used, els, title=D["dash_title"], maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "This week at a glance")
    tx = _text(g, used, els, "A static snapshot of the latest {cat} numbers.".format(
        cat=g.choice(D["cats"]).lower()), "muted")
    grd = _grid(g, used, els, 2, "md")
    m1 = _metric(g, used, els, l1, v1)
    m2 = _metric(g, used, els, l2, v2)
    brow = _stack(g, used, els, "horizontal", "sm")
    bd = _badge(g, used, els, status, "outline")
    btn = _button(g, used, els, "Refresh snapshot", "secondary", "refresh_data", {})
    els[brow]["children"] = [bd, btn]
    els[grd]["children"] = [m1, m2]
    els[stk]["children"] = [hd, tx, grd, brow]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Static {thing} snapshot card: {m1}, {m2}, a {s} badge, refresh button.".format(
            thing=D["thing"], m1=l1, m2=l2, s=status.lower()),
        "verbose": ("Just a simple static overview for {thing}, no interactivity needed: "
                    "show {m1} at {v1} and {m2} at {v2}, a small {s} status chip, and a "
                    "refresh button for later.").format(
            thing=D["thing"], m1=l1, v1=v1, m2=l2, v2=v2, s=status.lower()),
        "imperative": ("Make a stateless snapshot panel for {thing} with {m1} and {m2} "
                       "figures, a {s} status chip, and a refresh action.").format(
            thing=D["thing"], m1=l1, m2=l2, s=status.lower()),
        "casual": ("no fancy stuff, just a {thing} snapshot: {m1} n {m2}, status chip, "
                   "refresh btn").format(thing=D["thing"], m1=l1, m2=l2),
    }
    return {"root": root, "elements": els}, tasks


def _dash_progress_alert(g, D):
    els, used = {}, set()
    l1, v1, c1, t1 = D["kpis"][0]
    l2, v2, c2, t2 = D["kpis"][1]
    load = g.randint(35, 92)
    al_title, al_msg, al_type = D["alerts"][g.randrange(len(D["alerts"]))]
    state = {"primary": v1, "primaryChange": c1, "primaryTrend": t1,
             "secondary": v2, "secondaryChange": c2, "secondaryTrend": t2,
             "capacity": load, "degraded": False}
    root = _card(g, used, els, title=D["dash_title"], maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "Capacity watch")
    grd = _grid(g, used, els, 2, "md")
    m1 = _metric(g, used, els, l1, {"$state": "/primary"}, {"$state": "/primaryChange"},
                 {"$state": "/primaryTrend"})
    m2 = _metric(g, used, els, l2, {"$state": "/secondary"}, {"$state": "/secondaryChange"},
                 {"$state": "/secondaryTrend"})
    pg = _progress(g, used, els, {"$state": "/capacity"}, 100, "Capacity used")
    al = _alert(g, used, els, al_title, al_msg, al_type,
                visible={"$state": "/degraded", "eq": True})
    els[grd]["children"] = [m1, m2]
    els[stk]["children"] = [hd, grd, pg, al]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "{thing} load view: {m1}, {m2}, capacity bar, alert only when degraded.".format(
            thing=D["thing"], m1=l1, m2=l2),
        "verbose": ("I want a capacity watch for {thing}. Two metrics - {m1} and {m2} - a "
                    "capacity bar, and an alert that only appears when the system is "
                    "flagged as degraded.").format(thing=D["thing"], m1=l1, m2=l2),
        "imperative": ("Show {m1} and {m2}, a capacity progress bar, and an error alert "
                       "that stays hidden unless degraded mode is on.").format(m1=l1, m2=l2),
        "casual": ("{thing} status page w/ a capacity bar + an alert that shows up only "
                   "if things go bad").format(thing=D["thing"]),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _dash_three_up(g, D):
    els, used = {}, set()
    k1, k2, k3 = D["kpis"][0], D["kpis"][1], D["kpis"][2]
    al_title, al_msg, al_type = D["alerts"][g.randrange(len(D["alerts"]))]
    state = {"a": k1[1], "aChange": k1[2], "aTrend": k1[3],
             "b": k2[1], "bChange": k2[2], "bTrend": k2[3],
             "c": k3[1], "cChange": k3[2], "cTrend": k3[3],
             "series": _series_state(D), "outage": False}
    root = _card(g, used, els, title=D["dash_title"], maxWidth="lg")
    stk = _stack(g, used, els, "vertical", "lg")
    hd = _heading(g, used, els, "Today so far")
    grd = _grid(g, used, els, 3, "md")
    m1 = _metric(g, used, els, k1[0], {"$state": "/a"}, {"$state": "/aChange"},
                 {"$state": "/aTrend"})
    m2 = _metric(g, used, els, k2[0], {"$state": "/b"}, {"$state": "/bChange"},
                 {"$state": "/bTrend"})
    m3 = _metric(g, used, els, k3[0], {"$state": "/c"}, {"$state": "/cChange"},
                 {"$state": "/cTrend"})
    cht = _graph(g, used, els, {"$state": "/series"}, D["series_title"])
    al = _alert(g, used, els, al_title, al_msg, al_type,
                visible={"$state": "/outage", "eq": True})
    els[grd]["children"] = [m1, m2, m3]
    els[stk]["children"] = [hd, grd, cht, al]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Three KPIs ({m1}, {m2}, {m3}) + {sl} chart; banner alert if outage.".format(
            m1=k1[0], m2=k2[0], m3=k3[0], sl=D["series_label"]),
        "verbose": ("Build the daily board for {thing}: a row of three numbers - {m1}, "
                    "{m2}, {m3} - then the {sl} chart, and a banner alert reserved for "
                    "outages.").format(thing=D["thing"], m1=k1[0], m2=k2[0], m3=k3[0],
                                       sl=D["series_label"]),
        "imperative": ("Lay out {m1}, {m2}, and {m3} in a three-column row, add the {sl} "
                       "chart, and wire an alert that only shows during an outage.").format(
            m1=k1[0], m2=k2[0], m3=k3[0], sl=D["series_label"]),
        "casual": ("3 stats side by side ({m1}/{m2}/{m3}), chart under, outage banner "
                   "hidden till needed").format(m1=k1[0], m2=k2[0], m3=k3[0]),
    }
    return {"root": root, "elements": els, "state": state}, tasks


# ------------------------------------------------------------- settings variants


def _set_basic(g, D):
    els, used = {}, set()
    state = {"fullName": D["people"][0], "email": "casey@" + D["cats"][0].lower() + ".io",
             "role": ""}
    root = _card(g, used, els, title="Account settings",
                 desc="Update your basic profile details.", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "Profile")
    ni = _input(g, used, els, "Full name", "fullName", "text", "Your name",
                {"$bindState": "/fullName"},
                [{"type": "required", "message": "Name is required"}])
    ei = _input(g, used, els, "Email", "email", "email", "you@example.com",
                {"$bindState": "/email"})
    ro = _select(g, used, els, "Role", "role", D["roles"], "Choose a role",
                 {"$bindState": "/role"})
    sv = _button(g, used, els, "Save changes", "primary", "save_form", {})
    els[stk]["children"] = [hd, ni, ei, ro, sv]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Settings form: name, email, {role} dropdown, save.".format(
            role=D["roles"][0].lower()),
        "verbose": ("I'd like an account settings panel where I can edit my full name and "
                    "email, pick my role from a dropdown, and hit save. Name should be "
                    "required."),
        "imperative": ("Build a profile settings form with name and email inputs, a role "
                       "selector, and a save button. Name is mandatory."),
        "casual": ("settings page thingy - name + email + role picker + save btn, name "
                   "can't be blank"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _set_two_col(g, D):
    els, used = {}, set()
    state = {"fullName": D["people"][1], "email": "sam@" + D["cats"][1].lower() + ".org",
             "bio": "", "isPublic": True}
    root = _card(g, used, els, title="Edit profile", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "Contact details")
    grd = _grid(g, used, els, 2, "md")
    ni = _input(g, used, els, "Full name", "fullName", "text", None,
                {"$bindState": "/fullName"})
    ei = _input(g, used, els, "Email", "email", "email", None, {"$bindState": "/email"})
    ta = _el(els, used, g, "ta", "Textarea",
             {"label": "Bio", "name": "bio", "rows": 4, "value": {"$bindState": "/bio"}})
    sw = _switch(g, used, els, "List me publicly", "public", {"$bindState": "/isPublic"})
    sv = _button(g, used, els, "Save profile", "primary", "save_form", {})
    els[grd]["children"] = [ni, ei]
    els[stk]["children"] = [hd, grd, ta, sw, sv]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Profile editor: name+email row, bio box, public toggle, save.",
        "verbose": ("A profile editor for {thing}'s member area: name and email side by "
                    "side, a multi-line bio underneath, a toggle for public listing, and "
                    "a save button.").format(thing=D["thing"]),
        "imperative": ("Compose an edit-profile screen: two-column name/email, bio "
                       "textarea, public-listing switch, save action."),
        "casual": ("edit profile plz - name/email next 2 each other, bio textarea, public "
                   "switch, save"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _set_prefs(g, D):
    els, used = {}, set()
    state = {"emailAlerts": True, "smsAlerts": False, "digest": "weekly", "dirty": False}
    root = _card(g, used, els, title="Notification preferences", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "How we reach you")
    sw1 = _switch(g, used, els, "Email alerts", "emailAlerts",
                  {"$bindState": "/emailAlerts"})
    sw2 = _switch(g, used, els, "SMS alerts", "smsAlerts", {"$bindState": "/smsAlerts"})
    se = _select(g, used, els, "Digest frequency", "digest",
                 ["daily", "weekly", "monthly"], None, {"$bindState": "/digest"})
    al = _alert(g, used, els, "Unsaved changes",
                "Toggle something to enable saving.", "info",
                visible={"$state": "/dirty", "eq": True})
    sv = _button(g, used, els, "Save preferences", "primary", "save_form", {})
    els[stk]["children"] = [hd, sw1, sw2, se, sv]
    els[root]["children"] = [stk, al]
    tasks = {
        "terse": "Prefs: email+SMS toggles, digest dropdown, hint until dirty, save.",
        "verbose": ("A notification preferences panel with an email toggle, an SMS toggle, "
                    "a digest-frequency dropdown, a save button, and a little info note "
                    "that only appears once something has been changed."),
        "imperative": ("Create a preferences form: email and SMS switches, digest "
                       "frequency select, save button; show an info alert only when the "
                       "dirty flag is set."),
        "casual": ("notif settings pls: mail/sms toggles, how-often dropdown, save btn, n "
                   "a tiny hint that shows after i change stuff"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _set_plan(g, D):
    els, used = {}, set()
    state = {"plan": "", "budget": 20, "tos": False}
    root = _card(g, used, els, title="Workspace preferences", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "Plan & limits")
    rd = _el(els, used, g, "rd", "Radio",
             {"label": "Plan", "name": "plan", "options": ["Starter", "Pro", "Team"],
              "value": {"$bindState": "/plan"}})
    sl = _el(els, used, g, "sl", "Slider",
             {"label": "Seat budget", "min": 5, "max": 100, "step": 5, "value": 20})
    ck = _el(els, used, g, "ck", "Checkbox",
             {"label": "I accept the terms", "name": "tos",
              "checked": {"$bindState": "/tos"}})
    sv = _button(g, used, els, "Apply", "primary", "save_form", {})
    els[stk]["children"] = [hd, rd, sl, ck, sv]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Plan picker (radio), seat-budget slider, terms checkbox, apply.",
        "verbose": ("For our workspace settings I need a plan radio group (Starter, Pro, "
                    "Team), a seat budget slider from 5 to 100, a terms checkbox bound to "
                    "a state flag, and an apply button."),
        "imperative": ("Assemble a plan preferences form: radio plan choice, budget "
                       "slider (5-100, step 5), TOS checkbox, apply button."),
        "casual": ("workspace setup: pick a plan, drag the seat budget, tick the tos box, "
                   "hit apply"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _set_danger(g, D):
    els, used = {}, set()
    state = {"confirmOpen": False}
    root = _card(g, used, els, title="Danger zone", maxWidth="md",
                 desc="These actions cannot be undone.")
    stk = _stack(g, used, els, "vertical", "md")
    tx = _text(g, used, els, "Deleting your workspace removes all " + D["cats"][0].lower()
               + " data permanently.", "muted")
    bopen = _button(g, used, els, "Delete workspace", "danger", "setState",
                    {"statePath": "/confirmOpen", "value": True})
    dl = _el(els, used, g, "dlg", "Dialog",
             {"title": "Are you sure?",
              "description": "This permanently removes the workspace.",
              "openPath": "/confirmOpen"},
             children=[])
    tx2 = _text(g, used, els, "This cannot be undone.", "body")
    bc = _button(g, used, els, "Cancel", "secondary", "setState",
                 {"statePath": "/confirmOpen", "value": False})
    bd = _button(g, used, els, "Yes, delete", "danger", "setState",
                 {"statePath": "/confirmOpen", "value": False})
    els[dl]["children"] = [tx2, bc, bd]
    els[stk]["children"] = [tx, bopen, dl]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Danger zone: delete button opens a confirm dialog with cancel/confirm.",
        "verbose": ("I need a danger-zone panel with a red delete button. Clicking it "
                    "opens a confirmation dialog explaining the action, with cancel and "
                    "confirm buttons that both close it."),
        "imperative": ("Create a delete-workspace control: the button toggles a "
                       "confirmation dialog open via state; cancel and confirm close it."),
        "casual": ("big red delete btn that pops a r u sure dialog, cancel + confirm "
                   "both close it"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


# ------------------------------------------------------------- todo variants


def _todo_classic(g, D):
    els, used = {}, set()
    n = g.randint(2, 4)
    items = [{"id": "t{0}".format(i + 1), "title": g.choice(D["tasks"]),
              "done": g.random() < 0.3} for i in range(n)]
    state = {"newItemText": "", "items": items}
    root = _card(g, used, els, title=g.choice(["Task list", "Today's tasks", "Checklist"]),
                 maxWidth="md")
    nw = _input(g, used, els, "New task", "newItem", "text", "What needs doing?",
                {"$bindState": "/newItemText"})
    ad = _button(g, used, els, "Add task", "primary", "pushState",
                 {"statePath": "/items", "value": {"$state": "/newItemText"},
                  "title": {"$state": "/newItemText"}, "id": "$id"})
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/items", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "title"}
    bd = _badge(g, used, els, "Done", "secondary",
                visible={"$item": "done", "eq": True})
    els[itm]["children"] = [bd]
    els[root]["children"] = [nw, ad, lst]
    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Task list with an add input; done items get a chip.",
        "verbose": ("A small task list for {thing}: type a task, hit add, and it joins the "
                    "list. Tasks already marked done show a little Done chip next to "
                    "them.").format(thing=D["thing"]),
        "imperative": ("Build a checklist: an input bound to the draft text, an add button "
                       "that appends to the list, and a done chip that only shows on "
                       "completed items."),
        "casual": ("lil to-do thing - type, add, n done ones get a lil chip ok?"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _todo_filter(g, D):
    els, used = {}, set()
    n = g.randint(3, 5)
    items = [{"id": "t{0}".format(i + 1), "title": g.choice(D["tasks"]),
              "priority": g.choice(PRIORITIES)} for i in range(n)]
    state = {"newItemText": "", "items": items, "priority": ""}
    root = _card(g, used, els, title="Priority board", maxWidth="md")
    nw = _input(g, used, els, "New task", "newItem", "text", "Add something...",
                {"$bindState": "/newItemText"})
    ad = _button(g, used, els, "Add", "primary", "pushState",
                 {"statePath": "/items", "value": {"$state": "/newItemText"},
                  "title": {"$state": "/newItemText"},
                  "priority": {"$state": "/priority"}, "id": "$id"})
    hint = _alert(g, used, els, "Pick a priority first",
                  "Choose a priority so the new task lands in the right bucket.",
                  "info", visible={"$state": "/newItemText", "neq": ""})
    row = _stack(g, used, els, "horizontal", "sm")
    se = _select(g, used, els, "Priority for new tasks", "priority", PRIORITIES,
                 "Select priority", {"$bindState": "/priority"})
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/items", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "title"}
    els[itm]["props"]["description"] = None
    bd = _badge(g, used, els, {"$item": "priority"}, "outline")
    els[itm]["children"] = [bd]
    rm = _button(g, used, els, "Remove top task", "secondary", "removeState",
                 {"statePath": "/items", "index": 0})
    els[row]["children"] = [se, ad]
    els[root]["children"] = [nw, row, hint, lst, rm]
    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Priority task board: input+priority, add, remove-top, badge per item.",
        "verbose": ("A priority board for {thing} tasks. New tasks get a typed title and a "
                    "chosen priority; adding appends to the list. Each row shows its "
                    "priority chip, and there's a button to knock the top task off.").format(
            thing=D["thing"]),
        "imperative": ("Create a task board: text input plus priority select feeding an "
                       "add button that pushes into the list, priority badges on each "
                       "card, and a remove-first control."),
        "casual": ("task tracker w/ priorities - type it, pick hi/med/low, add it. also "
                   "a 'remove top' button for cleanup"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _todo_progress(g, D):
    els, used = {}, set()
    n = g.randint(2, 4)
    items = [{"id": "t{0}".format(i + 1), "title": g.choice(D["tasks"]),
              "pct": g.randint(10, 95)} for i in range(n)]
    state = {"items": items, "openCount": n}
    root = _card(g, used, els, title="In progress", maxWidth="md")
    hd = _heading(g, used, els, "Work in flight")
    tx = _text(g, used, els, "{n} items in the {cat} queue.".format(
        n=n, cat=g.choice(D["cats"]).lower()), "muted")
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/items", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "title"}
    pg = _progress(g, used, els, {"$item": "pct"}, 100, None)
    els[itm]["children"] = [pg]
    els[root]["children"] = [hd, tx, lst]
    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Queue view: each task card shows its own progress bar.",
        "verbose": ("Show our in-flight work as cards, one per item, each with the task "
                    "name and its own progress bar so we can see how far along everything "
                    "is."),
        "imperative": ("Render the work queue: a repeating list of task cards, each "
                       "embedding that item's completion percentage as a bar."),
        "casual": ("cards w/ a progress bar in each one, % straight from the data plz"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _todo_board(g, D):
    els, used = {}, set()
    n = g.randint(3, 5)
    items = [{"id": "t{0}".format(i + 1), "title": g.choice(D["tasks"]),
              "status": g.choice(D["statuses"])} for i in range(n)]
    state = {"items": items}
    root = _card(g, used, els, title="Status board", maxWidth="md")
    hd = _heading(g, used, els, "By status")
    tx = _text(g, used, els, "{n} tasks tracked across the board.".format(n=n), "muted")
    tabs = _el(els, used, g, "tbs", "Tabs",
               {"tabs": [{"label": "Open", "value": "open"},
                         {"label": "All", "value": "all"}],
                "defaultValue": "all"}, children=[])
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/items", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "title"}
    els[itm]["props"]["description"] = {"$item": "status"}
    els[tabs]["children"] = [lst]
    els[root]["children"] = [hd, tx, tabs]
    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Status board with Open/All tabs; each row lists task + status.",
        "verbose": ("A simple board for {thing}: tabs to switch between Open and All, and "
                    "a list where every task shows its current status under the "
                    "title.").format(thing=D["thing"]),
        "imperative": ("Make a tabbed status board; under the tabs, repeat the task cards "
                       "with each task's status as its sub-line."),
        "casual": ("tabs (open/all) + task rows w/ the status under the title, easy"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


# ------------------------------------------------------------- profile variants


def _prof_basic(g, D):
    els, used = {}, set()
    person = g.choice(D["people"])
    skills = g.sample(D["cats"], 2)
    pct = g.randint(40, 95)
    root = _card(g, used, els, maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md", align="center")
    av = _el(els, used, g, "av", "Avatar", {"name": person, "size": "lg"})
    hd = _heading(g, used, els, person, "h2")
    tx = _text(g, used, els, g.choice([
        "{cat} specialist based in the region.",
        "Ten years across {cat} and operations.",
        "Leads the {cat} team."]).format(cat=g.choice(D["cats"]).lower()), "muted")
    brow = _stack(g, used, els, "horizontal", "sm")
    b1 = _badge(g, used, els, skills[0], "default")
    b2 = _badge(g, used, els, skills[1], "outline")
    pg = _progress(g, used, els, pct, 100, "Profile completeness")
    els[brow]["children"] = [b1, b2]
    els[stk]["children"] = [av, hd, tx, brow, pg]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Profile card: avatar, name, blurb, two chips, completeness bar.",
        "verbose": ("A member profile card centered on the page: large avatar, the name, "
                    "a one-line bio, two skill chips, and a completeness meter at the "
                    "bottom."),
        "imperative": ("Compose a profile card with an avatar, heading, muted bio text, a "
                       "horizontal badge row, and a progress meter."),
        "casual": ("cute lil profile card w/ avatar, name, chips n a progress thing"),
    }
    return {"root": root, "elements": els}, tasks


def _prof_faq(g, D):
    els, used = {}, set()
    person = g.choice(D["people"])
    root = _card(g, used, els, title="About " + person.split()[-1], maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, person)
    tx = _text(g, used, els, "Answers to what teammates ask most.", "muted")
    ac = _el(els, used, g, "acc", "Accordion",
             {"items": [
                 {"title": "Background?",
                  "content": "Ten years in " + g.choice(D["cats"]).lower() + "."},
                 {"title": "Office hours?",
                  "content": "Weekdays 10:00-12:00, or by appointment."},
                 {"title": "How to reach?",
                  "content": "Message app first; email for anything formal."}]},
             children=[])
    tg = _el(els, used, g, "tg", "ToggleGroup",
             {"items": [{"label": "Bio", "value": "bio"},
                        {"label": "FAQ", "value": "faq"},
                        {"label": "Contact", "value": "contact"}],
              "type": "single", "value": "faq"}, children=[])
    els[stk]["children"] = [hd, tx, tg, ac]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Mini profile: name, blurb, view switcher, FAQ accordion.",
        "verbose": ("A small about-panel for {who}: their name, a muted blurb, a segmented "
                    "switcher (Bio / FAQ / Contact), and an accordion with the three most "
                    "common questions.").format(who=person),
        "imperative": ("Build an about panel with a name heading, caption text, a "
                       "single-select toggle group, and a 3-item FAQ accordion."),
        "casual": ("about panel: name, blurb, lil switcher, n an accordion faq"),
    }
    return {"root": root, "elements": els}, tasks


def _prof_activity(g, D):
    els, used = {}, set()
    person = g.choice(D["people"])
    cols = ["When", "Activity", "Detail"]
    rows = [[g.choice(["Mon", "Tue", "Wed", "Thu"]), g.choice(D["tasks"]),
             g.choice(D["statuses"])] for _ in range(g.randint(3, 4))]
    state = {"cols": cols, "rows": rows}
    root = _card(g, used, els, title="Recent activity", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, person)
    tx = _text(g, used, els, "Latest moves this week.", "muted")
    tbl = _table(g, used, els, {"$state": "/cols"}, {"$state": "/rows"})
    ln = _el(els, used, g, "ln", "Link",
             {"label": "View full history", "href": "/history/" + person.split()[-1].lower()})
    els[stk]["children"] = [hd, tx, tbl, ln]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Activity card: name, note, week table, history link.",
        "verbose": ("For {who}'s page: their name, a one-liner, a small table of this "
                    "week's activity (when, what, status), and a link to the full "
                    "history.").format(who=person),
        "imperative": ("Create an activity summary card with a name heading, caption, a "
                       "three-column table driven from state, and a history link."),
        "casual": ("card w/ name + this week's stuff as a table + a 'full history' link"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _prof_actions(g, D):
    els, used = {}, set()
    person = g.choice(D["people"])
    state = {"following": False, "composerOpen": False}
    root = _card(g, used, els, maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md", align="center")
    av = _el(els, used, g, "av", "Avatar", {"name": person, "size": "lg"})
    hd = _heading(g, used, els, person, "h2")
    rt = _el(els, used, g, "rt", "Rating", {"value": g.randint(3, 5), "max": 5,
                                            "label": "Peer rating"})
    brow = _stack(g, used, els, "horizontal", "sm")
    b1 = _button(g, used, els, "Follow", "primary", "setState",
                 {"statePath": "/following", "value": True})
    b2 = _button(g, used, els, "Message", "secondary", "setState",
                 {"statePath": "/composerOpen", "value": True})
    dlg = _el(els, used, g, "dlg", "Dialog",
              {"title": "Message " + person.split()[0],
               "description": "Write them a short note - it lands in their DMs.",
               "openPath": "/composerOpen"},
              children=[])
    dtx = _text(g, used, els, "The composer opens in a light-weight panel.", "body")
    els[brow]["children"] = [b1, b2]
    els[dlg]["children"] = [dtx]
    els[stk]["children"] = [av, hd, rt, brow, dlg]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Profile: avatar, name, rating, follow + message buttons opening a dialog.",
        "verbose": ("A teammate card for {who}: avatar and name up top, a peer rating, "
                    "then Follow and Message buttons; Message flips a state flag that "
                    "opens the composer dialog.").format(who=person),
        "imperative": ("Create a profile card with avatar, rating, and two buttons that "
                       "set state; the Message button opens a dialog keyed on its flag."),
        "casual": ("profile card: avatar, stars, follow btn + msg btn (msg pops a lil "
                   "dialog)"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


# -------------------------------------------------------- notifications variants


def _notif_toggle(g, D):
    els, used = {}, set()
    on_t, on_m, _ = D["alerts"][0]
    off_t, off_m, _ = D["alerts"][1]
    state = {"alertsOn": True}
    root = _card(g, used, els, title="Alerts", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "Notification center")
    sw = _switch(g, used, els, "Show alerts", "alerts", {"$bindState": "/alertsOn"})
    a1 = _alert(g, used, els, on_t, on_m, "warning",
                visible={"$state": "/alertsOn", "eq": True})
    a2 = _alert(g, used, els, off_t, off_m, "success",
                visible={"$state": "/alertsOn", "eq": False})
    els[stk]["children"] = [hd, sw, a1, a2]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Alert toggle: warning alert while on, success note while off.",
        "verbose": ("A tiny notification center: a switch that turns alerts on or off. "
                    "While on, show the {t} warning; while off, show a friendly "
                    "all-clear instead.").format(t=on_t.lower()),
        "imperative": ("Bind a switch to the alerts flag and gate two alerts on it: the "
                       "warning shows when true, the success note when false."),
        "casual": ("on/off switch for alerts - warning when on, chill all-clear when "
                   "off"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _notif_list(g, D):
    els, used = {}, set()
    n = g.randint(3, 5)
    kinds = ["info", "warning", "error", "success"]
    notes = [{"id": "n{0}".format(i + 1),
              "title": D["alerts"][i % len(D["alerts"])][0],
              "kind": g.choice(kinds)} for i in range(n)]
    state = {"filter": "", "unread": g.randint(3, 40), "notes": notes}
    root = _card(g, used, els, title="Inbox", maxWidth="md")
    hd = _heading(g, used, els, "Notifications")
    se = _select(g, used, els, "Filter by kind", "kindFilter", kinds, "All kinds",
                 {"$bindState": "/filter"})
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/notes", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "title"}
    bd = _badge(g, used, els, {"$item": "kind"}, "outline")
    els[itm]["children"] = [bd]
    btn = _button(g, used, els, "Mark all read", "secondary", "setState",
                  {"statePath": "/unread", "value": 0})
    els[root]["children"] = [hd, se, lst, btn]
    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Inbox: kind filter, note list w/ kind chips, mark-all-read.",
        "verbose": ("Build an inbox panel: a dropdown to filter by kind, the list of "
                    "notifications each with its kind chip, and a button that zeroes the "
                    "unread counter."),
        "imperative": ("Create a notifications list bound to state with a kind select "
                       "filter, per-item badges, and a mark-all-read action."),
        "casual": ("notif list w/ a filter dropdown n kind chips + 'mark all read' plz"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _notif_sev(g, D):
    els, used = {}, set()
    state = {"severity": g.choice(["info", "warning", "critical"]), "escalate": False}
    root = _card(g, used, els, title="Health", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "System status")
    sw = _switch(g, used, els, "Escalate page", "escalate", {"$bindState": "/escalate"})
    a1 = _alert(g, used, els, "Critical incident",
                "Pager engaged; on-call has been paged.", "error",
                visible={"$state": "/severity", "eq": "critical"})
    a2 = _alert(g, used, els, "All systems normal",
                "No active incidents right now.", "success",
                visible={"$state": "/severity", "neq": "critical"})
    els[stk]["children"] = [hd, sw, a1, a2]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Status card: critical banner vs normal note, plus escalate switch.",
        "verbose": ("A status card for {thing}: when severity is critical show the "
                    "incident banner, otherwise the all-normal note. Add an escalate "
                    "switch for paging.").format(thing=D["thing"]),
        "imperative": ("Gate two alerts on the severity value (eq critical / neq "
                       "critical) and bind an escalate switch."),
        "casual": ("status thing: red banner only if critical, green note otherwise + "
                   "pager switch"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _notif_details(g, D):
    els, used = {}, set()
    t, m, ty = D["alerts"][g.randrange(len(D["alerts"]))]
    state = {"dismissed": False}
    root = _card(g, used, els, title="Alert details", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    al = _alert(g, used, els, t, m, ty)
    cl = _el(els, used, g, "cl", "Collapsible",
             {"title": "Technical details", "defaultOpen": False}, children=[])
    dtx = _text(g, used, els, "Source: monitor-{n}. Region: {r}.".format(
        n=g.randint(2, 9), r=g.choice(["us-east", "eu-west", "ap-south"])), "caption")
    btn = _button(g, used, els, "Dismiss", "secondary", "setState",
                  {"statePath": "/dismissed", "value": True})
    bye = _el(els, used, g, "bye", "Text",
              {"text": "Alert dismissed. It stays hidden until the next occurrence.",
               "variant": "muted"},
              visible={"$state": "/dismissed", "eq": True})
    els[cl]["children"] = [dtx]
    els[stk]["children"] = [al, cl, btn, bye]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Alert w/ collapsible tech details + dismiss; note once dismissed.",
        "verbose": ("Show the {t} alert with a collapsible section hiding technical "
                    "details, a dismiss button, and after dismissing a small note saying "
                    "it's hidden until next time.").format(t=t.lower()),
        "imperative": ("Compose an alert card: collapsible details drawer, dismiss button "
                       "that sets a flag, and a confirmation note bound to that flag."),
        "casual": ("alert card w/ a 'details' dropdown, dismiss btn, n a lil bye-bye "
                   "note after"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


# ------------------------------------------------------------- pricing variants


def _price_grid(g, D):
    els, used = {}, set()
    names = g.sample(PLANS, 3)
    root = _card(g, used, els, title="Plans", maxWidth="lg",
                 desc="Simple pricing, cancel anytime.")
    grd = _grid(g, used, els, 3, "md")
    els[root]["children"] = [grd]
    popular = g.randrange(3)
    for i, name in enumerate(names):
        pc = _card(g, used, els, title=name, maxWidth="full")
        hd = _heading(g, used, els, PRICES[i], "h3")
        btn = _button(g, used, els, "Choose " + name, "primary" if i == popular else "secondary")
        kids = []
        if i == popular:
            bd = _badge(g, used, els, "Most popular", "default")
            kids.append(bd)
        kids += [hd, btn]
        els[pc]["children"] = kids
        els[grd]["children"].append(pc)
    tasks = {
        "terse": "Three plan cards w/ price + CTA; mark one popular.",
        "verbose": ("A pricing section with three plan cards side by side - {a}, {b}, {c} "
                    "- each showing its price and a choose button. Highlight one as most "
                    "popular.").format(a=names[0], b=names[1], c=names[2]),
        "imperative": ("Lay out three pricing cards in a grid with price headings and "
                       "choose buttons; badge the featured plan."),
        "casual": ("3 pricing cards ({a}/{b}/{c}) w/ prices n buttons, lil 'popular' "
                   "badge on one").format(a=names[0], b=names[1], c=names[2]),
    }
    return {"root": root, "elements": els}, tasks


def _price_billing(g, D):
    els, used = {}, set()
    names = g.sample(PLANS, 3)
    state = {"billing": "monthly"}
    root = _card(g, used, els, title="Plans", maxWidth="lg")
    hd = _heading(g, used, els, "Pick your plan", "h2")
    tg = _el(els, used, g, "tg", "ToggleGroup",
             {"items": [{"label": "Monthly", "value": "monthly"},
                        {"label": "Yearly", "value": "yearly"}],
              "type": "single", "value": "monthly"}, children=[])
    grd = _grid(g, used, els, 3, "md")
    for i, name in enumerate(names):
        pc = _card(g, used, els, title=name, maxWidth="full")
        hd2 = _heading(g, used, els, PRICES[i], "h3")
        btn = _button(g, used, els, "Choose " + name, "secondary")
        els[pc]["children"] = [hd2, btn]
        els[grd]["children"].append(pc)
    els[root]["children"] = [hd, tg, grd]
    tasks = {
        "terse": "Plans w/ monthly/yearly switcher on top.",
        "verbose": ("Pricing panel with a monthly/yearly segmented switch at the top and "
                    "the three plan cards ({a}, {b}, {c}) below; the switch value lives "
                    "in state.").format(a=names[0], b=names[1], c=names[2]),
        "imperative": ("Add a billing-cycle toggle group bound to state above a "
                       "three-card plan grid."),
        "casual": ("monthly/yearly toggle then the 3 plan cards, tia"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _price_compare(g, D):
    els, used = {}, set()
    names = g.sample(PLANS, 2)
    cols = ["Feature", names[0], names[1]]
    rows = [[f, "Yes" if g.random() < 0.7 else "-", "Yes" if g.random() < 0.5 else "-"]
            for f in g.sample(FEATURES, 4)]
    state = {"cols": cols, "rows": rows}
    root = _card(g, used, els, title="Compare plans", maxWidth="lg")
    hd = _heading(g, used, els, names[0] + " vs " + names[1])
    grd = _grid(g, used, els, 2, "md")
    for i, name in enumerate(names):
        pc = _card(g, used, els, title=name, maxWidth="full")
        hd2 = _heading(g, used, els, PRICES[i], "h3")
        btn = _button(g, used, els, "Choose " + name, "primary")
        els[pc]["children"] = [hd2, btn]
        els[grd]["children"].append(pc)
    tbl = _table(g, used, els, {"$state": "/cols"}, {"$state": "/rows"})
    els[root]["children"] = [hd, grd, tbl]
    tasks = {
        "terse": "Two plan cards + feature comparison table.",
        "verbose": ("A comparison view for {a} vs {b}: both plan cards with price and CTA, "
                    "then a feature matrix underneath pulled from state.").format(
            a=names[0], b=names[1]),
        "imperative": ("Show two plan cards, then a state-driven comparison table of "
                       "features with yes/dash cells."),
        "casual": ("{a} vs {b} - two cards up top, feature table under").format(
            a=names[0], b=names[1]),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _price_faq(g, D):
    els, used = {}, set()
    names = g.sample(PLANS, 2)
    root = _card(g, used, els, title="Plans & FAQ", maxWidth="lg")
    hd = _heading(g, used, els, "Simple pricing")
    grd = _grid(g, used, els, 2, "md")
    for i, name in enumerate(names):
        pc = _card(g, used, els, title=name, maxWidth="full")
        hd2 = _heading(g, used, els, PRICES[i], "h3")
        btn = _button(g, used, els, "Choose " + name, "primary")
        els[pc]["children"] = [hd2, btn]
        els[grd]["children"].append(pc)
    ac = _el(els, used, g, "acc", "Accordion",
             {"items": [
                 {"title": "Can I switch later?",
                  "content": "Yes, upgrades apply immediately; downgrades at renewal."},
                 {"title": "Refunds?",
                  "content": "14-day money-back, no questions asked."},
                 {"title": "Seats?",
                  "content": "Add or remove seats any time; billing prorates."}]},
             children=[])
    ln = _el(els, used, g, "ln", "Link",
             {"label": "Talk to sales", "href": "/sales"}, children=[])
    els[root]["children"] = [hd, grd, ac, ln]
    tasks = {
        "terse": "Two plans, FAQ accordion, talk-to-sales link.",
        "verbose": ("Pricing page with two plan cards ({a}, {b}) and beneath them an FAQ "
                    "accordion covering switching, refunds, and seats, plus a contact "
                    "link.").format(a=names[0], b=names[1]),
        "imperative": ("Build the pricing block: plan cards, then a three-question FAQ "
                       "accordion and a sales link."),
        "casual": ("plans + lil faq accordion + 'talk to sales' link ty"),
    }
    return {"root": root, "elements": els}, tasks


# -------------------------------------------------------------- search variants


def _search_classic(g, D):
    els, used = {}, set()
    n = g.randint(2, 4)
    results = [{"id": str(i + 1), "name": p, "meta": g.choice(D["statuses"]) + " - "
                + g.choice(D["cats"])} for i, p in enumerate(g.sample(D["products"], n))]
    state = {"query": "", "page": 1, "results": results}
    root = _card(g, used, els, title="Search", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "Find it fast")
    inp = _input(g, used, els, "Search", "query", "text", "Type to search...",
                 {"$bindState": "/query"})
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/results", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "name"}
    els[itm]["props"]["description"] = {"$item": "meta"}
    pg = _el(els, used, g, "pg", "Pagination",
             {"totalPages": g.randint(3, 9), "page": {"$bindState": "/page"}},
             children=[], on={"change": {"action": "load_data", "params": {}}})
    els[stk]["children"] = [hd, inp, lst, pg]
    els[root]["children"] = [stk]
    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Search box + result cards + pager.",
        "verbose": ("A search page for {thing}: the query box drives the results list, "
                    "each result shows its name and a status/category line, and paging "
                    "loads the next page.").format(thing=D["thing"]),
        "imperative": ("Create a search panel: input bound to the query, a repeated "
                       "results list, and pagination that triggers a data load on "
                       "change."),
        "casual": ("search thingy: type -> results, w/ page numbers at the bottom"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _search_rated(g, D):
    els, used = {}, set()
    n = g.randint(2, 4)
    results = [{"id": str(i + 1), "name": p, "rating": g.randint(3, 5)}
               for i, p in enumerate(g.sample(D["products"], n))]
    state = {"cat": "", "results": results}
    root = _card(g, used, els, title="Browse", maxWidth="md")
    hd = _heading(g, used, els, "Top picks")
    se = _select(g, used, els, "Category", "cat", D["cats"], "All categories",
                 {"$bindState": "/cat"})
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/results", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "name"}
    rt = _el(els, used, g, "rt", "Rating", {"value": {"$item": "rating"}, "max": 5},
             children=[])
    els[itm]["children"] = [rt]
    els[root]["children"] = [hd, se, lst]
    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Category filter + rated result cards.",
        "verbose": ("A browsing panel: pick a category from the dropdown and the cards "
                    "below each show their name with a star rating straight from the "
                    "data."),
        "imperative": ("Build a filterable list: category select bound to state, repeated "
                       "cards, each embedding the item's rating."),
        "casual": ("pick a category -> cards w/ stars on each, ty"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _search_stateless(g, D):
    els, used = {}, set()
    l1, v1, _, _ = D["kpis"][2]
    l2, v2, _, _ = D["kpis"][3]
    root = _card(g, used, els, title="Quick find", maxWidth="md")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "Look up a record")
    inp = _input(g, used, els, "Record", "lookup", "text", "ID or name...")
    btn = _button(g, used, els, "Search", "primary", "refresh_data", {})
    grd = _grid(g, used, els, 2, "sm")
    m1 = _metric(g, used, els, l1, v1)
    m2 = _metric(g, used, els, l2, v2)
    tx = _text(g, used, els, "Searches cover the last 90 days of " +
               g.choice(D["cats"]).lower() + " records.", "caption")
    els[grd]["children"] = [m1, m2]
    els[stk]["children"] = [hd, inp, btn, grd, tx]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Lookup box + search button; two reference stats under.",
        "verbose": ("A minimal lookup card: one input, a search button that refreshes "
                    "data, and a couple of reference stats ({m1}, {m2}) for context.").format(
            m1=l1, m2=l2),
        "imperative": ("Create a stateless lookup panel: input, search action, and a "
                       "two-stat context row."),
        "casual": ("simple: type an id, hit search, couple stats below"),
    }
    return {"root": root, "elements": els}, tasks


def _search_sorted(g, D):
    els, used = {}, set()
    n = g.randint(2, 3)
    results = [{"id": str(i + 1), "name": p} for i, p in enumerate(g.sample(D["products"], n))]
    state = {"query": "", "results": results}
    root = _card(g, used, els, title="Catalog", maxWidth="md")
    hd = _heading(g, used, els, "Browse the catalog")
    row = _stack(g, used, els, "horizontal", "sm")
    inp = _input(g, used, els, "Search", "query", "text", "Type to filter...",
                 {"$bindState": "/query"})
    dm = _el(els, used, g, "dm", "DropdownMenu",
             {"label": "Sort", "items": [{"label": "Newest", "value": "new"},
                                         {"label": "A-Z", "value": "az"},
                                         {"label": "Top rated", "value": "top"}],
              "value": "new"}, children=[])
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/results", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "name"}
    img = _el(els, used, g, "img", "Image", {"alt": {"$item": "name"},
                                             "width": 96, "height": 96}, children=[])
    els[itm]["children"] = [img]
    els[row]["children"] = [inp, dm]
    els[root]["children"] = [hd, row, lst]
    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Catalog: search box + sort dropdown; image per result.",
        "verbose": ("A catalog browser with a search input and a sort dropdown (newest, "
                    "A-Z, top rated) in one row, then result cards that each show the "
                    "item's image."),
        "imperative": ("Assemble a browse bar (query input + sort DropdownMenu) over a "
                       "repeating card list; each card renders the item image using the "
                       "item's name as alt."),
        "casual": ("search + sort dropdown in a row, then cards w/ lil pics"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


# -------------------------------------------------------------- orders variants


def _orders_export(g, D):
    els, used = {}, set()
    cols = ["Order", "Customer", "Total", "Status"]
    rows = [[str(1000 + i), p, "$" + str(g.randint(15, 480)), g.choice(D["statuses"])]
            for i, p in enumerate(g.sample(D["people"], g.randint(3, 5)))]
    state = {"cols": cols, "rows": rows}
    root = _card(g, used, els, title="Recent orders", maxWidth="lg")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, D["dash_title"])
    tbl = _table(g, used, els, {"$state": "/cols"}, {"$state": "/rows"},
                 "Last 7 days")
    brow = _stack(g, used, els, "horizontal", "sm")
    b1 = _button(g, used, els, "Export report", "secondary", "export_report", {})
    b2 = _button(g, used, els, "Refresh", "secondary", "refresh_data", {})
    els[brow]["children"] = [b1, b2]
    els[stk]["children"] = [hd, tbl, brow]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Orders table + export/refresh buttons.",
        "verbose": ("An orders table for {thing} with customer, total and status columns, "
                    "and export plus refresh buttons underneath.").format(thing=D["thing"]),
        "imperative": ("Create a state-driven orders table with a caption, and a button "
                       "row: export report and refresh."),
        "casual": ("orders table pls, w/ export n refresh btns under"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _orders_filter(g, D):
    els, used = {}, set()
    cols = ["Order", "Customer", "Total", "Status"]
    rows = [[str(2000 + i), p, "$" + str(g.randint(15, 480)), g.choice(D["statuses"])]
            for i, p in enumerate(g.sample(D["people"], g.randint(3, 5)))]
    state = {"statusFilter": "", "cols": cols, "rows": rows}
    root = _card(g, used, els, title="Order desk", maxWidth="lg")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "Filter the queue")
    se = _select(g, used, els, "Status", "statusFilter", D["statuses"], "All statuses",
                 {"$bindState": "/statusFilter"})
    tbl = _table(g, used, els, {"$state": "/cols"}, {"$state": "/rows"})
    al = _alert(g, used, els, "Held orders need attention",
                "Some rows are held at the hub; review before end of day.", "warning",
                visible={"$state": "/statusFilter", "eq": "Held"})
    els[stk]["children"] = [hd, se, tbl, al]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Orders w/ status filter; warning banner while 'Held' is picked.",
        "verbose": ("An order desk view: a status dropdown filters the table, and while "
                    "the Held status is selected a warning banner reminds us to review "
                    "those orders before end of day."),
        "imperative": ("Bind a status select over the orders table and show a warning "
                       "alert only when the filter equals Held."),
        "casual": ("filter orders by status; if i pick 'held' show me the nag banner"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _orders_cards(g, D):
    els, used = {}, set()
    n = g.randint(3, 5)
    orders = [{"id": str(3000 + i), "customer": p,
               "total": "$" + str(g.randint(15, 480)),
               "status": g.choice(D["statuses"])}
              for i, p in enumerate(g.sample(D["people"], n))]
    state = {"page": 1, "orders": orders}
    root = _card(g, used, els, title="Latest orders", maxWidth="md")
    hd = _heading(g, used, els, "Fresh from the queue")
    lst = _stack(g, used, els, "vertical", "sm",
                 repeat={"statePath": "/orders", "key": "id"})
    itm = _card(g, used, els, maxWidth="full")
    els[itm]["props"]["title"] = {"$item": "customer"}
    els[itm]["props"]["description"] = {"$item": "total"}
    bd = _badge(g, used, els, {"$item": "status"}, "outline")
    els[itm]["children"] = [bd]
    pg = _el(els, used, g, "pg", "Pagination",
             {"totalPages": g.randint(2, 6), "page": {"$bindState": "/page"}}, children=[])
    els[root]["children"] = [hd, lst, pg]
    els[lst]["children"] = [itm]
    tasks = {
        "terse": "Order cards (name, status chip, total) + pager.",
        "verbose": ("Instead of a table, show recent orders as cards - customer name as "
                    "the title, a status chip and total in a row - with pagination at "
                    "the bottom."),
        "imperative": ("Render orders as repeating cards with a status badge and total, "
                       "and bind a paginator underneath."),
        "casual": ("order cards not a table plz - chip + total on each, pagey at bottom"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


def _orders_tabs(g, D):
    els, used = {}, set()
    cols = ["Order", "Customer", "Total", "Status"]
    rows = [[str(4000 + i), p, "$" + str(g.randint(15, 480)), g.choice(D["statuses"])]
            for i, p in enumerate(g.sample(D["people"], g.randint(3, 5)))]
    state = {"cols": cols, "rows": rows}
    root = _card(g, used, els, title="Order history", maxWidth="lg")
    stk = _stack(g, used, els, "vertical", "md")
    hd = _heading(g, used, els, "All orders")
    tabs = _el(els, used, g, "tbs", "Tabs",
               {"tabs": [{"label": "All", "value": "all"},
                         {"label": "Open", "value": "open"},
                         {"label": "Closed", "value": "closed"}],
                "defaultValue": "all"}, children=[])
    tbl = _table(g, used, els, {"$state": "/cols"}, {"$state": "/rows"})
    brow = _stack(g, used, els, "horizontal", "sm")
    b1 = _button(g, used, els, "Export report", "secondary", "export_report", {})
    b2 = _button(g, used, els, "Refresh", "secondary", "refresh_data", {})
    al = _alert(g, used, els, "Archived rows",
                "Orders older than 90 days move to the archive.", "info")
    els[brow]["children"] = [b1, b2]
    els[tabs]["children"] = [tbl]
    els[stk]["children"] = [hd, tabs, brow, al]
    els[root]["children"] = [stk]
    tasks = {
        "terse": "Order history under All/Open/Closed tabs + export/refresh buttons.",
        "verbose": ("Order history with tabs for All, Open, and Closed; the table itself "
                    "lives inside the tab panel and reads its columns and rows from "
                    "state, with export and refresh buttons under the tabs."),
        "imperative": ("Create a tabbed order history where the table is nested inside "
                       "the tabs element, plus an export/refresh button row."),
        "casual": ("tabs (all/open/closed) w/ the orders table inside + export n refresh "
                   "btns, ty"),
    }
    return {"root": root, "elements": els, "state": state}, tasks


VARIANTS = {
    "dashboard_metrics": [_dash_overview, _dash_table, _dash_stateless,
                          _dash_progress_alert, _dash_three_up],
    "settings_form": [_set_basic, _set_two_col, _set_prefs, _set_plan, _set_danger],
    "todo_list": [_todo_classic, _todo_filter, _todo_progress, _todo_board],
    "profile_card": [_prof_basic, _prof_faq, _prof_activity, _prof_actions],
    "notifications_center": [_notif_toggle, _notif_list, _notif_sev, _notif_details],
    "pricing_cards": [_price_grid, _price_billing, _price_compare, _price_faq],
    "search_results": [_search_classic, _search_rated, _search_stateless, _search_sorted],
    "orders_table": [_orders_export, _orders_filter, _orders_cards, _orders_tabs],
}

PLAN = [("dashboard_metrics", 63), ("settings_form", 63), ("todo_list", 63),
        ("profile_card", 63), ("notifications_center", 62), ("pricing_cards", 62),
        ("search_results", 62), ("orders_table", 62)]


# ------------------------------------------------------- structural self-checks


def _bounds_check(spec):
    """Return a list of budget problems (element count, depth, siblings)."""
    els = spec["elements"]
    root = spec["root"]
    parent = {}
    for k, el in els.items():
        for c in el.get("children", []):
            parent[c] = k
    def depth(k):
        n, cur, seen = 0, k, set()
        while cur in parent:
            if cur in seen:
                return 99
            seen.add(cur)
            n += 1
            cur = parent[cur]
        return n
    problems = []
    n = len(els)
    if not (6 <= n <= 16):
        problems.append("element_count={0}".format(n))
    d = max(depth(k) for k in els) + 1
    if d > 4:
        problems.append("depth={0}".format(d))
    sib = max((len(el.get("children", [])) for el in els.values()), default=0)
    if sib > 5:
        problems.append("siblings={0}".format(sib))
    if root not in els:
        problems.append("root_missing")
    return problems


def _features(spec):
    blob = json.dumps(spec)
    feats = []
    if "state" not in spec:
        feats.append("stateless")
    if "$bindState" in blob:
        feats.append("bindState")
    if '"visible"' in blob:
        feats.append("visible")
    if '"repeat"' in blob:
        feats.append("repeat")
    if '"pushState"' in blob:
        feats.append("pushState")
    if '"setState"' in blob:
        feats.append("setState")
    if '"removeState"' in blob:
        feats.append("removeState")
    return feats


def main():
    g = random.Random(240924)
    built = []
    for arch, count in PLAN:
        variants = VARIANTS[arch]
        for i in range(count):
            variant = variants[i % len(variants)]
            domain = DOMAIN_KEYS[(i // len(variants)) % len(DOMAIN_KEYS)]
            tone = TONES[i % len(TONES)]
            D = DOMAINS[domain]
            spec, tasks = variant(g, D)
            task = tasks[tone]
            built.append((arch, domain, tone, task, spec))

    rows, fails = [], []
    feat_hist, dom_hist, tone_hist = {}, {}, {}
    for arch, domain, tone, task, spec in built:
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
            fails.append((arch, task, problems))
            continue
        rows.append({"arch_hint": arch, "task": task, "spec": spec, "split": "train"})
        for f in _features(spec):
            feat_hist[f] = feat_hist.get(f, 0) + 1
        dom_hist[domain] = dom_hist.get(domain, 0) + 1
        tone_hist[tone] = tone_hist.get(tone, 0) + 1

    os.makedirs(OUT_DIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, separators=(",", ":"), ensure_ascii=False) + "\n")

    arch_hist = {}
    for r in rows:
        arch_hist[r["arch_hint"]] = arch_hist.get(r["arch_hint"], 0) + 1

    print("rows={0} fails={1} out={2}".format(len(rows), len(fails), OUT))
    print("per_arch=" + json.dumps(arch_hist, sort_keys=True))
    print("per_domain=" + json.dumps(dom_hist, sort_keys=True))
    print("per_tone=" + json.dumps(tone_hist, sort_keys=True))
    print("features=" + json.dumps(feat_hist, sort_keys=True))
    for arch, task, problems in fails[:15]:
        print("FAIL", arch, "|", task[:60], "|", "; ".join(problems[:4]))


if __name__ == "__main__":
    main()
