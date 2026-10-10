#!/usr/bin/env python3
"""Synthetic 12-month dataset for "Northside Physio" -- a FICTIONAL clinic.

Every person, email, phone number and invoice is invented. Emails use the
reserved example.* domains; phones use Ofcom's drama range (07700 900xxx).
No network, stdlib only, deterministic for a given seed.

Writes (flat, next to this file by default; gitignored):
  leakage_data_gmail.json    inbox-shaped enquiries (messy names/emails/phones)
  leakage_data_cliniko.json  Cliniko-shaped patients + appointments
  leakage_data_xero.json     Xero-shaped invoices + payments
  leakage_data_truth.json    true identities + the planted leaks

Planted leak types (plus look-alike decoys that are NOT leaks):
  enquiry_no_response     never answered (or answered >48h) and no booking
  response_no_booking     high-intent, answered once, never chased, no booking
  attendance_lapse        no-show/cancel never rebooked, or plan abandoned
  delivered_not_invoiced  attended appointment with no invoice
  invoiced_not_paid       invoice unpaid, or insurer short-paid, well past due
"""
import argparse
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 42
START = datetime(2025, 10, 1)
AS_OF = datetime(2026, 9, 30, 23, 59)
N_PERSONS = 1290
PLANTED = {"t1": 55, "t2": 50, "t3a": 30, "t3b": 30, "t4": 40, "t5a": 25, "t5b": 30}
INSURERS = ["Bupa", "AXA Health", "Vitality", "Aviva"]
CLINIC = "Northside Physio (FICTIONAL)"

FIRST = ("James Oliver Harry Jack George Noah Leo Arthur Oscar Archie Henry Thomas Edward William "
         "Daniel Samuel Joseph Matthew Alexander Christopher Michael Robert Richard Stephen Anthony "
         "Olivia Amelia Isla Ava Emily Isabella Mia Poppy Ella Lily Sophie Grace Evie Charlotte "
         "Jessica Ruby Chloe Freya Daisy Alice Elizabeth Katherine Rebecca Jennifer Margaret Hannah "
         "Laura Sarah Emma Lucy Megan Rachel Natalie Zoe Priya Aisha Fatima Tariq Imran Rahul Ananya "
         "Wei Mei Kofi Ade").split()
LAST = ("Smith Jones Taylor Brown Williams Wilson Johnson Davies Robinson Wright Thompson Evans Walker "
        "White Roberts Green Hall Wood Jackson Clarke Patel Khan Ahmed Ali Hussain Lewis Hughes Morgan "
        "Edwards Turner Hill Moore Cooper King Baker Harris Ward Morris Watson Parker Clark Cook Bailey "
        "Bell Murphy Kelly Shaw Collins Marshall Simpson Mitchell Phillips Stewart Campbell Mills Price "
        "Fox Hunt Palmer Wells Chapman Webb Ellis Lawson Gibson Ford Knight Pearce Dixon Bennett Barnes "
        "Fisher Reid Armstrong Bates Holmes Carr Hawkins Fletcher Gardner Burns Hayes Lane Owen "
        "Okafor Mensah Chen Singh Kaur Sharma Gupta Nowak Kowalski Rossi Silva").split()
NICK = {"robert": ["bob", "rob"], "william": ["will", "bill"], "elizabeth": ["liz", "beth"],
        "james": ["jim", "jamie"], "katherine": ["kate", "katie"], "thomas": ["tom"],
        "margaret": ["maggie"], "michael": ["mike"], "alexander": ["alex"], "christopher": ["chris"],
        "samuel": ["sam"], "daniel": ["dan"], "matthew": ["matt"], "rebecca": ["becky"],
        "jennifer": ["jen"], "edward": ["ed"], "anthony": ["tony"], "stephen": ["steve"],
        "joseph": ["joe"], "richard": ["rich"]}
DOMAINS = ["example.com", "example.org", "example.net", "example.co.uk"]

HIGH_MSGS = [
    "Hi, I'd like to book an appointment for my {body}. What's your earliest availability?",
    "Hello - {body} has been getting worse. Can anyone see me this week? Happy to book.",
    "Please could I book a first appointment? {body}, need to be seen asap.",
    "Do you have availability next week? I'd like to book in for {body}.",
]
LOW_MSGS = [
    "How much do you charge for an initial session? Just comparing options for {body}.",
    "Do you treat this kind of thing? Not sure yet, just researching {body}.",
    "What are your opening hours and prices? Thinking about it for {body}.",
    "Quick question about costs for {body}.",
]
BODIES_PHYSIO = ["lower back pain", "knee pain after running", "a stiff neck", "shoulder injury",
                 "sciatica", "ankle sprain", "tennis elbow", "hip pain"]
BODIES_AES = ["anti-wrinkle treatment", "dermal filler", "lip filler consultation", "skin rejuvenation"]
SPAM = ["Boost your clinic's Google ranking with our SEO packages!!",
        "We can supply discount medical gloves in bulk, reply for a quote",
        "Guest post opportunity - sponsored link placement for your website"]


def iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def with_time(rng, d):
    return d.replace(hour=rng.randint(8, 18), minute=rng.randint(0, 59), second=0, microsecond=0)


def typo(rng, s):
    if len(s) < 4:
        return s
    i = rng.randint(1, len(s) - 2)
    kind = rng.choice(["drop", "swap", "dup"])
    if kind == "drop":
        return s[:i] + s[i + 1:]
    if kind == "swap":
        return s[:i] + s[i + 1] + s[i] + s[i + 2:]
    return s[:i] + s[i] + s[i:]


def mess_name(rng, f, l):
    r = rng.random()
    if r < 0.38:
        return f"{f} {l}"
    if r < 0.50:
        return f"{f} {l}".lower()
    if r < 0.55:
        return f"{f} {l}".upper()
    if r < 0.64:
        return f"{l}, {f}"
    if r < 0.74:
        return f"{f[0]} {l}"
    if r < 0.84 and f.lower() in NICK:
        return f"{rng.choice(NICK[f.lower()]).title()} {l}"
    if r < 0.92:
        return f"{typo(rng, f)} {l}"
    return f"{f} {typo(rng, l)}"


def mess_email(rng, e):
    r = rng.random()
    if r < 0.60:
        return e
    if r < 0.75:
        return e.upper()
    if r < 0.85:
        return " " + e + " "
    local, dom = e.split("@")
    head, tail = dom.split(".", 1)
    return f"{local}@{typo(rng, head)}.{tail}"


def mess_phone(rng, ph):
    d = ph.replace(" ", "")
    r = rng.random()
    if r < 0.35:
        return f"{d[:5]} {d[5:]}"
    if r < 0.55:
        return d
    if r < 0.80:
        return "+44 " + d[1:5] + " " + d[5:]
    if r < 0.90:
        return f"(0){d[1:5]}-{d[5:8]}-{d[8:]}"
    return f"{d[:5]}.{d[5:]}"


def make_persons(rng):
    phones = [f"07700 900{n:03d}" for n in range(1000)]
    rng.shuffle(phones)
    persons = []
    for i in range(N_PERSONS):
        f, l = rng.choice(FIRST), rng.choice(LAST)
        local = rng.choice([f"{f}.{l}", f"{f[0]}{l}", f"{f}{l}", f"{l}.{f}"]).lower() + str(rng.randint(1, 99))
        persons.append({
            "pid": f"PER-{i:04d}", "first": f, "last": l,
            "email": f"{local}@{rng.choice(DOMAINS)}",
            "email_alt": f"{f}{rng.randint(100, 999)}@{rng.choice(DOMAINS)}".lower() if rng.random() < 0.3 else None,
            "phone": phones.pop() if phones and rng.random() < 0.8 else None})
    for k in range(40):  # households: shared surname + email (sometimes phone) -> hard cases
        a, b = persons[k * 7], persons[N_PERSONS - 1 - k * 3]
        b["last"], b["email"] = a["last"], a["email"]
        if rng.random() < 0.5 and a["phone"]:
            b["phone"] = a["phone"]
    return persons


def gen(seed=SEED):
    rng = random.Random(seed)
    persons = make_persons(rng)
    span = (datetime(2026, 9, 20) - START).total_seconds()
    for p in persons:
        p["E"] = START + timedelta(seconds=rng.random() * span)
    early = [p for p in persons if p["E"] < datetime(2026, 7, 10)]
    rng.shuffle(early)
    roles = {}

    def take(role, n, cutoff=None):
        got = [p for p in early if p["pid"] not in roles and (cutoff is None or p["E"] < cutoff)][:n]
        for p in got:
            roles[p["pid"]] = role

    take("t1", PLANTED["t1"])
    take("t2", PLANTED["t2"])
    for r in ("t3a", "t3b", "t4", "t5a", "t5b"):
        take(r, PLANTED[r], datetime(2026, 6, 25))

    enquiries, appts, patients, leaks = [], [], {}, []
    chans = ["web_form"] * 55 + ["email"] * 30 + ["phone"] * 15

    def enquiry(p, ts, text, outbound, first_resp):
        chan = rng.choice(chans)
        email = p["email_alt"] if (p["email_alt"] and rng.random() < 0.15) else p["email"]
        e = {"person": p["pid"], "received_at": iso(ts), "channel": chan,
             "name_raw": mess_name(rng, p["first"], p["last"]),
             "email_raw": None if (chan == "phone" and rng.random() < 0.6) else mess_email(rng, email),
             "phone_raw": mess_phone(rng, p["phone"]) if (p["phone"] and (chan == "phone" or rng.random() < 0.35)) else None,
             "message": text, "outbound_count": outbound,
             "first_response_at": iso(first_resp) if first_resp else None}
        enquiries.append(e)

    conv_roles = ("t3a", "t3b", "t4", "t5a", "t5b")
    for p in persons:
        role = roles.get(p["pid"])
        aes = rng.random() < 0.25
        body = rng.choice(BODIES_AES if aes else BODIES_PHYSIO)
        high = role in ("t2",) + conv_roles or rng.random() < 0.35
        text = rng.choice(HIGH_MSGS if high else LOW_MSGS).format(body=body)
        E = p["E"]
        late = False
        if role == "t1":
            lag = None if rng.random() < 0.6 else rng.uniform(72, 130)
            conv = False
        else:
            late = role is None and rng.random() < 0.05
            lag = rng.uniform(50, 110) if late else rng.uniform(0.2, 30)
            if role in conv_roles:
                conv = True
            elif role == "t2":
                conv = False
            else:
                conv = rng.random() < ((0.55 if high else 0.12) * (0.55 if late else 1))
        resp_ts = None if lag is None else E + timedelta(hours=lag)
        start = (resp_ts or E) + timedelta(days=rng.randint(1, 8))
        if conv and start > AS_OF:
            conv = False
        if resp_ts is None:
            outbound = 0
        elif role == "t2":
            outbound = 1
        elif conv:
            outbound = rng.choice([1, 2])
        else:
            outbound = 2 if high else 1  # high-intent non-converters were chased (decoys)
        if conv and role is None and rng.random() < 0.22 and E - timedelta(days=4) > START:
            enquiry(p, E - timedelta(days=rng.randint(1, 4)), text, 0, None)  # unanswered, then they chased
            enquiry(p, E, "Following up on my message from the other day - can I book an appointment?",
                    outbound, resp_ts)
        else:
            enquiry(p, E, text, outbound, resp_ts)
            late_lost = late and not conv and E <= AS_OF - timedelta(days=21)  # answered >48h, never booked
            if role in ("t1", "t2") or late_lost:
                leaks.append({"type": "response_no_booking" if role == "t2" else "enquiry_no_response",
                              "person": p["pid"], "_enq": len(enquiries) - 1})
        if not conv:
            continue

        # ---- Cliniko journey ----
        physio = (not aes) or role in ("t3a", "t3b", "t5b")
        plan_n = rng.choices([1, 4, 6, 8], [.2, .35, .3, .15])[0] if physio else rng.choices([1, 2], [.7, .3])[0]
        if role in ("t3a", "t3b"):
            plan_n = max(plan_n, 3)
        payer = "insurer" if (physio and (role == "t5b" or (role not in ("t5a",) and rng.random() < 0.30))) else "self"
        ptype = "Physio" if physio else rng.choice(["Anti-wrinkle", "Dermal filler"])
        fail_slot = rng.randint(1, plan_n) if role == "t3a" else None
        stop_after = rng.randint(1, plan_n - 1) if role == "t3b" else None
        pat = {"pid": p["pid"], "first_name": p["first"], "last_name": p["last"],
               "email": p["email_alt"] if (p["email_alt"] and rng.random() < 0.10) else p["email"],
               "phone": p["phone"] if rng.random() < 0.9 else None, "payer": payer,
               "insurer": rng.choice(INSURERS) if payer == "insurer" else None,
               "service": ptype, "role": role}
        my, dt, done, stop = [], with_time(rng, start), 0, False
        for slot in range(1, plan_n + 1):
            if stop:
                break
            attempts = 0
            while True:
                if dt > AS_OF:
                    stop = True
                    break
                price = (75 if slot == 1 else 55) if ptype == "Physio" else (180 if ptype == "Anti-wrinkle" else 320)
                r = rng.random()
                status = "attended" if r < 0.88 else ("did_not_arrive" if r < 0.94 else "cancelled")
                if attempts >= 2:
                    status = "attended"
                if fail_slot == slot:
                    status = rng.choice(["did_not_arrive", "cancelled"])
                my.append({"person": p["pid"], "starts_at": dt, "appointment_type": ptype,
                           "price": float(price), "payer": payer, "status": status})
                if status == "attended":
                    done += 1
                    dt = with_time(rng, dt + timedelta(days=rng.randint(5, 9)))
                    break
                if fail_slot == slot:
                    stop = True
                    break
                attempts += 1
                dt = with_time(rng, dt + timedelta(days=rng.randint(3, 10)))
            if stop_after is not None and done >= stop_after:
                break
        if not my:
            continue
        pat["plan"] = plan_n if role else max(done, 1)
        pat["created_at"] = iso(my[0]["starts_at"] - timedelta(hours=1))
        patients[p["pid"]] = pat
        appts.extend(my)
        if role in ("t3a", "t3b"):
            my[-1]["_leak"] = ("no_show_not_rebooked" if role == "t3a" else "plan_abandoned")

    appts.sort(key=lambda a: a["starts_at"])
    for n, a in enumerate(appts, 1):
        a["id"] = f"A-{n:05d}"
    first_seen = {}
    for a in appts:
        first_seen.setdefault(a["person"], a["starts_at"])
    pids = sorted(patients, key=lambda k: first_seen[k])
    pat_id = {k: f"P-{n:04d}" for n, k in enumerate(pids, 1)}
    for a in appts:
        a["patient_id"] = pat_id[a["person"]]
        if "_leak" in a:
            leaks.append({"type": "attendance_lapse", "subtype": a["_leak"], "key": a["id"], "person": a["person"]})

    # ---- Xero invoices + payments ----
    chosen = {}
    for a in appts:
        if a["status"] == "attended" and patients[a["person"]]["role"] in ("t4", "t5a", "t5b"):
            chosen.setdefault(a["person"], []).append(a["id"])
    chosen = {k: rng.choice(v) for k, v in chosen.items()}
    invs, claim = [], 88000
    for a in appts:
        if a["status"] != "attended":
            continue
        pat = patients[a["person"]]
        role = pat["role"]
        is_chosen = chosen.get(a["person"]) == a["id"]
        if role == "t4" and is_chosen:
            leaks.append({"type": "delivered_not_invoiced", "key": a["id"], "person": a["person"],
                          "value_hard": a["price"]})
            continue
        ins = a["payer"] == "insurer"
        inv_dt = min(a["starts_at"] + timedelta(days=rng.randint(0, 3) if ins else 0), AS_OF)
        if rng.random() < 0.72:
            ref = a["id"]
        elif ins:
            claim += rng.randint(1, 40)
            ref = f"{pat['last_name']} {pat['first_name'][0]} - claim {claim}"
        else:
            ref = f"{pat['service']} - {pat['last_name']} {pat['first_name'][0]}"
        if ins:
            cname, cemail = pat["insurer"], "claims@example.net"
        else:
            cname = mess_name(rng, pat["first_name"], pat["last_name"])
            cemail = pat["email"] if rng.random() < 0.4 else None
        amt = a["price"]
        pay_dt = inv_dt + timedelta(days=rng.randint(14, 40) if ins else rng.randint(0, 7))
        lk = None
        if role == "t5a" and is_chosen:
            amt, lk = 0.0, {"subtype": "unpaid_overdue", "value_hard": a["price"]}
        elif role == "t5b" and is_chosen:
            amt = round(a["price"] * rng.uniform(0.6, 0.85), 2)
            pay_dt = inv_dt + timedelta(days=rng.randint(14, 35))
            lk = {"subtype": "insurer_short_pay", "value_hard": round(a["price"] - amt, 2)}
        invs.append({"date": inv_dt, "due": inv_dt + timedelta(days=30), "total": a["price"],
                     "contact_name": cname, "contact_email": cemail, "reference": ref,
                     "_appt": a["id"], "_person": a["person"], "_lk": lk,
                     "_pay": (pay_dt, amt) if (amt > 0 and pay_dt <= AS_OF) else None})
    invs.sort(key=lambda i: i["date"])
    pays, gt_inv_person, gt_inv_appt = [], {}, {}
    for n, inv in enumerate(invs, 1):
        inv["invoice_id"], inv["number"] = f"INV-{n:05d}", f"NP-{n:05d}"
        gt_inv_person[inv["invoice_id"]] = inv["_person"]
        gt_inv_appt[inv["invoice_id"]] = inv["_appt"]
        if inv["_lk"]:
            leaks.append({"type": "invoiced_not_paid", "key": inv["invoice_id"], "person": inv["_person"],
                          **inv["_lk"]})
        if inv["_pay"]:
            pays.append({"payment_id": f"PAY-{len(pays) + 1:05d}", "invoice_id": inv["invoice_id"],
                         "date": iso(inv["_pay"][0]), "amount": round(inv["_pay"][1], 2),
                         "bank_ref": "CLINIC-STRIPE" if inv["contact_name"] not in INSURERS else inv["contact_name"].upper()})

    # ---- enquiries: add spam decoys, assign ids ----
    for _ in range(40):
        enquiries.append({"person": None, "received_at": iso(START + timedelta(seconds=rng.random() * span)),
                          "channel": "email", "name_raw": rng.choice(["SEO Team", "Bulk Supplies Ltd", "Growth Hacker"]),
                          "email_raw": f"promo{rng.randint(1, 999)}@example.net", "phone_raw": None,
                          "message": rng.choice(SPAM), "outbound_count": 0, "first_response_at": None})
    tagged = {id(enquiries[lk["_enq"]]): lk for lk in leaks if "_enq" in lk}
    enquiries.sort(key=lambda e: e["received_at"])
    gt_enq_person = {}
    for n, e in enumerate(enquiries, 1):
        e["enquiry_id"], e["thread_id"] = f"ENQ-{n:04d}", f"thr{n:06d}"
        gt_enq_person[e["enquiry_id"]] = e["person"]
        if id(e) in tagged:
            tagged[id(e)]["key"] = e["enquiry_id"]

    g = [{k: v for k, v in e.items() if k != "person"} for e in enquiries]
    c = {"patients": [{"id": pat_id[k], "first_name": patients[k]["first_name"], "last_name": patients[k]["last_name"],
                       "email": patients[k]["email"], "phone": patients[k]["phone"], "created_at": patients[k]["created_at"],
                       "treatment_plan_sessions": patients[k]["plan"], "payer": patients[k]["payer"],
                       "insurer": patients[k]["insurer"]} for k in pids],
         "appointments": [{"id": a["id"], "patient_id": a["patient_id"], "starts_at": iso(a["starts_at"]),
                           "appointment_type": a["appointment_type"], "price": a["price"], "payer": a["payer"],
                           "status": a["status"]} for a in appts]}
    x = {"invoices": [{"invoice_id": i["invoice_id"], "number": i["number"], "contact_name": i["contact_name"],
                       "contact_email": i["contact_email"], "reference": i["reference"], "date": iso(i["date"]),
                       "due_date": iso(i["due"]), "total": i["total"]} for i in invs],
         "payments": pays}
    t = {"clinic": CLINIC, "as_of": iso(AS_OF), "seed": seed, "enquiry_person": gt_enq_person,
         "patient_person": {v: k for k, v in pat_id.items()}, "invoice_person": gt_inv_person,
         "invoice_appointment": gt_inv_appt,
         "leaks": [{k: v for k, v in lk.items() if not k.startswith("_")} for lk in leaks]}
    return g, c, x, t


NAMES = ["gmail", "cliniko", "xero", "truth"]


def main(outdir=None, seed=SEED):
    outdir = Path(outdir) if outdir else Path(__file__).parent
    outdir.mkdir(parents=True, exist_ok=True)
    g, c, x, t = gen(seed)
    for name, obj in zip(NAMES, (g, c, x, t)):
        (outdir / f"leakage_data_{name}.json").write_text(json.dumps(obj, indent=1))
    counts = {}
    for lk in t["leaks"]:
        counts[lk["type"]] = counts.get(lk["type"], 0) + 1
    print(f"{CLINIC}: {len(g)} enquiries, {len(c['patients'])} patients, {len(c['appointments'])} appointments, "
          f"{len(x['invoices'])} invoices, {len(x['payments'])} payments")
    print("planted leaks:", counts)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args()
    main(a.out, a.seed)
