#!/usr/bin/env python3
"""Enquiry-to-cash leakage pipeline (synthetic data only, no network, stdlib).

normalise -> match identities across sources (deterministic, confidence-scored)
-> detect leaks with rules -> put a GBP value on each -> draft an action per leak.

Nothing here sends anything: every action is drafted with status
"awaiting approval". A human approves in the real product.
"""
import bisect
import difflib
import json
import re
from datetime import datetime, timedelta
from pathlib import Path

AUTO = 0.85       # >= AUTO: link automatically
REVIEW = 0.50     # REVIEW..AUTO: low confidence -> Gemini stub, else human review queue
RESPONSE_SLA_H = 48
BOOKING_WINDOW_D = 21
RECOVERY_FACTOR = 0.30   # assumption: share of a stale warm lead a chase recovers
INSURERS = {"bupa", "axa health", "vitality", "aviva"}
HIGH_WORDS = ("book", "appointment", "availab", "asap", "see me", "this week")
SPAM_WORDS = ("seo", "bulk", "guest post", "sponsored", "ranking")
NICK_GROUPS = [{"robert", "bob", "rob"}, {"william", "will", "bill"}, {"elizabeth", "liz", "beth"},
               {"james", "jim", "jamie"}, {"katherine", "kate", "katie"}, {"thomas", "tom"},
               {"margaret", "maggie"}, {"michael", "mike"}, {"alexander", "alex"},
               {"christopher", "chris"}, {"samuel", "sam"}, {"daniel", "dan"}, {"matthew", "matt"},
               {"rebecca", "becky"}, {"jennifer", "jen"}, {"edward", "ed"}, {"anthony", "tony"},
               {"stephen", "steve"}, {"joseph", "joe"}, {"richard", "rich"}]
HERE = Path(__file__).parent
DT = datetime.fromisoformat


# ---------------------------------------------------------------- normalise
def norm_email(s):
    s = (s or "").strip().lower()
    return s if "@" in s else None


def norm_phone(s):
    d = re.sub(r"\D", "", s or "")
    if d.startswith("44"):
        d = "0" + d[2:]
    return d if len(d) >= 10 else None


def parse_name(s):
    s = re.sub(r"[^A-Za-z,\s'-]", "", (s or "")).strip().lower()
    if "," in s:
        last, first = [x.strip() for x in s.split(",", 1)]
        return first.split()[0] if first else "", last
    t = s.split()
    if not t:
        return "", ""
    return (t[0], t[-1]) if len(t) > 1 else ("", t[0])


def _nick(a, b):
    return any(a in g and b in g for g in NICK_GROUPS)


def name_score(n1, n2):
    (f1, l1), (f2, l2) = n1, n2
    lr = difflib.SequenceMatcher(None, l1, l2).ratio()
    if f1 == f2:
        fr = 1.0
    elif _nick(f1, f2):
        fr = 0.95
    elif (len(f1) == 1 and f2.startswith(f1)) or (len(f2) == 1 and f1.startswith(f2)):
        fr = 0.85
    else:
        fr = difflib.SequenceMatcher(None, f1, f2).ratio()
    return 0.6 * lr + 0.4 * fr


def noisy_or(ps):
    q = 1.0
    for p in ps:
        q *= 1 - p
    return 1 - q


def evidence(name, email, phone, pat):
    """Return (confidence, name_score) for record-vs-patient."""
    parts = []
    pe = norm_email(pat.get("email"))
    if email and pe:
        if email == pe:
            parts.append(0.92)
        elif email.split("@")[0] == pe.split("@")[0]:
            parts.append(0.75)
        elif difflib.SequenceMatcher(None, email.split("@")[0], pe.split("@")[0]).ratio() >= 0.9:
            parts.append(0.45)
    contact_hit = bool(parts and parts[0] >= 0.9)
    pp = norm_phone(pat.get("phone"))
    if phone and pp and phone == pp:
        parts.append(0.90)
        contact_hit = True
    ns = name_score(name, (pat["first_name"].lower(), pat["last_name"].lower())) if name != ("", "") else 0.0
    parts.append(0.55 if ns >= 0.93 else 0.40 if ns >= 0.85 else 0.20 if ns >= 0.78 else 0.0)
    conf = noisy_or(parts)
    if contact_hit and ns < 0.80:   # shared household email/phone but the name disagrees
        conf = min(conf, 0.60)
    return conf, ns


def match_with_gemini(record, candidates):
    """STUB. In production: send the record plus the low-confidence candidates to
    Vertex Gemini (europe-west2, paid tier, no training on client data) with a
    structured-output schema {patient_id | null, confidence, reason}, and return that.
    Anything it returns below AUTO still goes to the human review queue.
    Offline demo: returns None, so every low-confidence pair stays in review."""
    return None


def resolve(name, email, phone, candidates, record):
    """candidates: list of patient dicts plausible by timing. Returns match dict."""
    scored = sorted(((*evidence(name, email, phone, p), p) for p in candidates), key=lambda x: -x[0])
    if not scored:
        return {"status": "none", "confidence": 0.0, "patient_id": None, "candidates": []}
    conf, ns, best = scored[0]
    plausible = [s for s in scored if s[1] >= 0.85]
    if ns >= 0.85 and len(plausible) == 1 and conf < 0.9 and conf >= 0.5:
        conf = noisy_or([conf, 0.70])        # only name-plausible patient in the time window
    if len(scored) > 1 and scored[1][0] >= conf - 0.05 and scored[1][2]["id"] != best["id"] and conf >= REVIEW:
        conf = min(conf, 0.60)               # ambiguous between two patients
    cands = [s[2]["id"] for s in scored if s[0] >= REVIEW - 0.1]
    if conf >= AUTO:
        return {"status": "auto", "confidence": round(conf, 3), "patient_id": best["id"], "candidates": cands}
    if conf >= REVIEW:
        g = match_with_gemini(record, [s[2] for s in scored[:3]])
        if g and g.get("patient_id"):
            return {"status": "review", "confidence": round(g.get("confidence", conf), 3),
                    "patient_id": g["patient_id"], "candidates": cands, "via": "gemini"}
        return {"status": "review", "confidence": round(conf, 3), "patient_id": None,
                "candidates": [s[2]["id"] for s in scored if s[0] >= REVIEW]}
    return {"status": "none", "confidence": round(conf, 3), "patient_id": None, "candidates": []}


# ---------------------------------------------------------------- pipeline
def load(indir):
    indir = Path(indir)
    rd = lambda n: json.loads((indir / f"leakage_data_{n}.json").read_text())
    return rd("gmail"), rd("cliniko"), rd("xero"), rd("truth")


def classify_intent(msg):
    m = msg.lower()
    if any(w in m for w in SPAM_WORDS):
        return "spam"
    return "high" if any(w in m for w in HIGH_WORDS) else "low"


def run(indir=None, outdir=None):
    indir = Path(indir) if indir else HERE
    outdir = Path(outdir) if outdir else indir
    gmail, cliniko, xero, truth = load(indir)
    as_of = DT(truth["as_of"])
    pats = {p["id"]: p for p in cliniko["patients"]}
    appts = sorted(cliniko["appointments"], key=lambda a: a["starts_at"])
    by_pat = {}
    for a in appts:
        by_pat.setdefault(a["patient_id"], []).append(a)

    # --- enquiry -> patient matching (candidates: first booking within 21d of enquiry)
    first = sorted((DT(v[0]["starts_at"]), k) for k, v in by_pat.items())
    first_ts = [f[0] for f in first]
    enq_match = {}
    for e in gmail:
        ts = DT(e["received_at"])
        lo, hi = bisect.bisect_left(first_ts, ts), bisect.bisect_right(first_ts, ts + timedelta(days=BOOKING_WINDOW_D))
        cands = [pats[first[i][1]] for i in range(lo, hi)]
        enq_match[e["enquiry_id"]] = resolve(parse_name(e["name_raw"]), norm_email(e["email_raw"]),
                                             norm_phone(e["phone_raw"]), cands, e)
        enq_match[e["enquiry_id"]]["_cand_all"] = [p["id"] for p in cands]

    # --- invoice -> appointment linking
    att = [a for a in appts if a["status"] == "attended"]
    att_ts = [DT(a["starts_at"]) for a in att]
    claimed, inv_match, withheld = {}, {}, set()
    invs = sorted(xero["invoices"], key=lambda i: i["date"])
    appt_ids = {a["id"] for a in appts}
    for inv in invs:
        if re.fullmatch(r"A-\d{5}", inv["reference"]) and inv["reference"] in appt_ids:
            claimed[inv["reference"]] = inv["invoice_id"]
            inv_match[inv["invoice_id"]] = {"status": "direct", "confidence": 1.0,
                                            "patient_id": None, "appt": inv["reference"]}
    for inv in invs:
        if inv["invoice_id"] in inv_match:
            continue
        d = DT(inv["date"])
        if " - claim " in inv["reference"]:
            l, f = inv["reference"].split(" - claim ")[0].lower().split()[:2]
            name, email = (f, l), None
        else:
            name, email = parse_name(inv["contact_name"]), norm_email(inv["contact_email"])
        lo, hi = bisect.bisect_left(att_ts, d - timedelta(days=21)), bisect.bisect_right(att_ts, d + timedelta(days=1))
        pid_set = {att[i]["patient_id"] for i in range(lo, hi)}
        m = resolve(name, email, None, [pats[x] for x in sorted(pid_set)], inv)
        inv_match[inv["invoice_id"]] = m
        if m["status"] == "auto":
            opts = [a for a in by_pat[m["patient_id"]] if a["status"] == "attended" and a["id"] not in claimed
                    and d - timedelta(days=21) <= DT(a["starts_at"]) <= d + timedelta(days=1)]
            opts.sort(key=lambda a: (abs(a["price"] - inv["total"]) > 1, abs((d - DT(a["starts_at"])).total_seconds())))
            if opts:
                claimed[opts[0]["id"]] = inv["invoice_id"]
                m["appt"] = opts[0]["id"]
        elif m["status"] == "review":
            for c in m["candidates"]:
                for a in by_pat[c]:
                    if d - timedelta(days=21) <= DT(a["starts_at"]) <= d + timedelta(days=1):
                        withheld.add(a["id"])

    # --- valuation parameters (from the data itself)
    ltv_list = [sum(a["price"] for a in v if a["status"] == "attended") for v in by_pat.values()]
    ltv = sum(ltv_list) / max(len(ltv_list), 1)
    fast = [e for e in gmail if classify_intent(e["message"]) != "spam" and e["outbound_count"] >= 1
            and e["first_response_at"] and (DT(e["first_response_at"]) - DT(e["received_at"])).total_seconds() / 3600 <= RESPONSE_SLA_H
            and DT(e["received_at"]) <= as_of - timedelta(days=BOOKING_WINDOW_D)]
    booked = lambda e: enq_match[e["enquiry_id"]]["status"] == "auto"
    conv_all = sum(booked(e) for e in fast) / max(len(fast), 1)
    hi_fast = [e for e in fast if classify_intent(e["message"]) == "high"]
    conv_high = sum(booked(e) for e in hi_fast) / max(len(hi_fast), 1)
    params = {"avg_patient_value_gbp": round(ltv, 2), "conv_rate_fast_response": round(conv_all, 3),
              "conv_rate_high_intent": round(conv_high, 3), "recovery_factor": RECOVERY_FACTOR}

    leaks = []

    def add(type_, key, value, basis, subtype=None, conf=1.0, **kw):
        leaks.append({"leak_id": f"L-{len(leaks) + 1:04d}", "type": type_, "subtype": subtype, "key": key,
                      "value_gbp": round(value, 2), "value_basis": basis, "confidence": round(conf, 3), **kw})

    # 1/2: enquiries
    for e in gmail:
        ts = DT(e["received_at"])
        intent = classify_intent(e["message"])
        m = enq_match[e["enquiry_id"]]
        if intent == "spam" or ts > as_of - timedelta(days=BOOKING_WINDOW_D) or m["status"] in ("auto", "review"):
            continue
        delay = ((DT(e["first_response_at"]) - ts).total_seconds() / 3600) if e["first_response_at"] else None
        conf = 1 - m["confidence"]
        if delay is None or delay > RESPONSE_SLA_H:
            add("enquiry_no_response", e["enquiry_id"], ltv * conv_all, "expected",
                "unanswered" if delay is None else "answered_late", conf, enquiry_id=e["enquiry_id"])
        elif intent == "high" and e["outbound_count"] == 1:
            add("response_no_booking", e["enquiry_id"], ltv * conv_high * RECOVERY_FACTOR, "expected",
                None, conf, enquiry_id=e["enquiry_id"])

    # 3: attendance lapse
    for pid, lst in by_pat.items():
        last = lst[-1]
        done = [a for a in lst if a["status"] == "attended"]
        avg_price = sum(a["price"] for a in done) / len(done) if done else lst[-1]["price"]
        plan = pats[pid]["treatment_plan_sessions"]
        ts = DT(last["starts_at"])
        if last["status"] != "attended" and ts <= as_of - timedelta(days=14):
            add("attendance_lapse", last["id"], max(plan - len(done), 1) * avg_price, "expected",
                "no_show_not_rebooked", patient_id=pid)
        elif last["status"] == "attended" and len(done) < plan and ts <= as_of - timedelta(days=28):
            add("attendance_lapse", last["id"], (plan - len(done)) * avg_price, "expected",
                "plan_abandoned", patient_id=pid)

    # 4: delivered, not invoiced
    for a in att:
        if a["id"] in claimed or a["id"] in withheld or DT(a["starts_at"]) > as_of - timedelta(days=7):
            continue
        add("delivered_not_invoiced", a["id"], a["price"], "hard", patient_id=a["patient_id"])

    # 5: invoiced, not paid
    paid = {}
    for p in xero["payments"]:
        paid[p["invoice_id"]] = paid.get(p["invoice_id"], 0) + p["amount"]
    for inv in invs:
        out = round(inv["total"] - paid.get(inv["invoice_id"], 0), 2)
        if out > 1 and as_of - DT(inv["due_date"]) >= timedelta(days=14):
            add("invoiced_not_paid", inv["invoice_id"], out, "hard",
                "unpaid_overdue" if inv["invoice_id"] not in paid else "short_paid", invoice_id=inv["invoice_id"])

    actions = [draft_action(l, gmail, pats, appts, invs, truth) for l in leaks]
    metrics = evaluate(leaks, enq_match, inv_match, gmail, invs, truth, pats, by_pat, as_of)
    metrics["params"] = params
    metrics["identity_review_queue"] = {
        "enquiries": sum(1 for m in enq_match.values() if m["status"] == "review"),
        "invoices": sum(1 for m in inv_match.values() if m["status"] == "review"),
        "appointments_withheld_pending_review": len(withheld)}
    outdir.mkdir(parents=True, exist_ok=True)
    for n, o in (("leaks", leaks), ("actions", actions), ("metrics", metrics)):
        (outdir / f"leakage_data_{n}.json").write_text(json.dumps(o, indent=1))
    return {"leaks": leaks, "actions": actions, "metrics": metrics}


# ---------------------------------------------------------------- actions
def _first(n):
    f = parse_name(n)[0]
    return f.title() if len(f) > 1 else "there"


def draft_action(l, gmail, pats, appts, invs, truth):
    clinic = "Northside Physio"
    t, to, ch, subj, body = l["type"], None, "email", "", ""
    if l.get("enquiry_id"):
        e = next(x for x in gmail if x["enquiry_id"] == l["enquiry_id"])
        to = norm_email(e["email_raw"]) or e["phone_raw"]
        ch = "email" if norm_email(e["email_raw"]) else "sms"
        nm = _first(e["name_raw"])
        if t == "enquiry_no_response":
            subj = "Sorry for the slow reply - can we help with your enquiry?"
            body = (f"Hi {nm}, apologies for not getting back to you sooner. We'd still love to help - "
                    f"we have appointments free this week. Reply YES and we'll hold a slot. - {clinic}")
        else:
            subj = "Still thinking about booking?"
            body = (f"Hi {nm}, just checking in after our reply. Would you like us to hold a first "
                    f"appointment for you this week? Reply with a day that suits. - {clinic}")
    elif t == "attendance_lapse":
        p = pats[l["patient_id"]]
        to = p["email"] or p["phone"]
        subj = "We missed you - shall we rebook?"
        body = (f"Hi {p['first_name']}, we noticed your treatment plan hasn't been completed "
                f"(about {int(l['value_gbp'] // 55) or 1} session(s) remain). Would you like us to book your next "
                f"visit? Reply with a day and time. - {clinic}")
    elif t == "delivered_not_invoiced":
        a = next(x for x in appts if x["id"] == l["key"])
        p = pats[a["patient_id"]]
        to, ch = "practice-manager (internal)", "xero_draft"
        subj = f"Raise invoice: {p['first_name']} {p['last_name']}, {a['starts_at'][:10]}"
        body = (f"Attended {a['appointment_type']} appointment {a['id']} on {a['starts_at'][:10]} "
                f"has no invoice. Draft invoice for GBP {a['price']:.2f} ({a['payer']}) ready to approve.")
    else:
        inv = next(x for x in invs if x["invoice_id"] == l["key"])
        to = inv["contact_email"] or inv["contact_name"]
        if inv["contact_name"].lower() in INSURERS:
            subj = f"Remittance query: invoice {inv['number']}"
            body = (f"Hello {inv['contact_name']} claims team, invoice {inv['number']} ({inv['reference']}) was for "
                    f"GBP {inv['total']:.2f}; GBP {l['value_gbp']:.2f} remains outstanding. Could you confirm the "
                    f"remittance and reason for the shortfall? - {clinic}")
        else:
            subj = f"Reminder: invoice {inv['number']}"
            body = (f"Hi {_first(inv['contact_name'])}, a friendly reminder that invoice {inv['number']} "
                    f"(GBP {l['value_gbp']:.2f} outstanding) was due on {inv['due_date'][:10]}. "
                    f"Payment details are on the invoice. - {clinic}")
    return {"action_id": "ACT-" + l["leak_id"][2:], "leak_id": l["leak_id"], "leak_type": t, "channel": ch,
            "to": to, "subject": subj, "body": body, "value_gbp": l["value_gbp"], "value_basis": l["value_basis"],
            "confidence": l["confidence"], "status": "awaiting approval"}


# ---------------------------------------------------------------- evaluation
def prf(tp, fp, fn):
    return {"tp": tp, "fp": fp, "fn": fn,
            "precision": round(tp / (tp + fp), 4) if tp + fp else None,
            "recall": round(tp / (tp + fn), 4) if tp + fn else None}


def evaluate(leaks, enq_match, inv_match, gmail, invs, truth, pats, by_pat, as_of):
    planted = {(l["type"], l["key"]) for l in truth["leaks"]}
    found = {(l["type"], l["key"]) for l in leaks}
    det = {}
    for t in sorted({p[0] for p in planted} | {f[0] for f in found}):
        P = {k for k in planted if k[0] == t}
        F = {k for k in found if k[0] == t}
        det[t] = prf(len(P & F), len(F - P), len(P - F))
    det["ALL"] = prf(len(planted & found), len(found - planted), len(planted - found))
    pat_of_person = {v: k for k, v in truth["patient_person"].items()}  # person -> patient id

    def link_stats(items):
        auto = correct = feasible = review = review_true = 0
        for true_pid, feas, m in items:
            if feas:
                feasible += 1
            if m["status"] == "auto":
                auto += 1
                correct += (m["patient_id"] == true_pid and true_pid is not None)
            elif m["status"] == "review":
                review += 1
                review_true += (true_pid in m["candidates"])
        return {"auto_links": auto, "correct": correct, "feasible_true_links": feasible,
                "precision": round(correct / auto, 4) if auto else None,
                "recall": round(correct / feasible, 4) if feasible else None,
                "sent_to_review": review, "review_contained_true_patient": review_true}

    e_items = []
    for e in gmail:
        person = truth["enquiry_person"][e["enquiry_id"]]
        tp = pat_of_person.get(person) if person else None
        e_items.append((tp, tp is not None and tp in enq_match[e["enquiry_id"]]["_cand_all"], enq_match[e["enquiry_id"]]))
    i_items = []
    for inv in invs:
        m = inv_match[inv["invoice_id"]]
        if m["status"] == "direct":
            continue
        tp = pat_of_person.get(truth["invoice_person"][inv["invoice_id"]])
        i_items.append((tp, True, m))
    both = e_items + i_items
    return {"detection": det, "matching": {"enquiry_to_patient": link_stats(e_items),
                                           "invoice_to_patient": link_stats(i_items),
                                           "combined": link_stats(both)}}


if __name__ == "__main__":
    r = run()
    for t, v in r["metrics"]["detection"].items():
        print(f"{t:26s} recall={v['recall']} precision={v['precision']} (tp={v['tp']} fp={v['fp']} fn={v['fn']})")
    print("matching:", r["metrics"]["matching"]["combined"])
    print(f"{len(r['leaks'])} leaks, {len(r['actions'])} drafted actions (all awaiting approval)")
