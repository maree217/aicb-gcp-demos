#!/usr/bin/env python3
"""Render a single static HTML "GBP at risk" page from pipeline output."""
import html
import json
from pathlib import Path

HERE = Path(__file__).parent
LABELS = {"enquiry_no_response": "1. Enquiry to response", "response_no_booking": "2. Response to booking",
          "attendance_lapse": "3. Booked to attended / rebooked", "delivered_not_invoiced": "4. Delivered to invoiced",
          "invoiced_not_paid": "5. Invoiced to paid"}
e = html.escape
pct = lambda v: "n/a" if v is None else f"{v * 100:.1f}%"
gbp = lambda v: f"&pound;{v:,.0f}"


def render(indir=None, out=None):
    d = Path(indir) if indir else HERE
    leaks = json.loads((d / "leakage_data_leaks.json").read_text())
    actions = {a["leak_id"]: a for a in json.loads((d / "leakage_data_actions.json").read_text())}
    m = json.loads((d / "leakage_data_metrics.json").read_text())
    rows, tot_h, tot_e = [], 0.0, 0.0
    for t, label in LABELS.items():
        ls = [l for l in leaks if l["type"] == t]
        h = sum(l["value_gbp"] for l in ls if l["value_basis"] == "hard")
        x = sum(l["value_gbp"] for l in ls if l["value_basis"] == "expected")
        tot_h, tot_e = tot_h + h, tot_e + x
        det = m["detection"].get(t, {})
        rows.append(f"<tr><td>{e(label)}</td><td class=n>{len(ls)}</td><td class=n>{gbp(h)}</td><td class=n>{gbp(x)}</td>"
                    f"<td class=n>{pct(det.get('recall'))}</td><td class=n>{pct(det.get('precision'))}</td></tr>")
    top = sorted(leaks, key=lambda l: -l["value_gbp"])[:10]
    trs = "".join(
        f"<tr><td>{e(LABELS[l['type']])}{' / ' + e(l['subtype']) if l['subtype'] else ''}</td>"
        f"<td class=n>&pound;{l['value_gbp']:,.2f} <small>({e(l['value_basis'])})</small></td>"
        f"<td>{e(actions[l['leak_id']]['subject'])}<br><small>to {e(str(actions[l['leak_id']]['to']))} - "
        f"{e(actions[l['leak_id']]['status'])}</small></td></tr>" for l in top)
    mt = m["matching"]
    mrows = "".join(f"<tr><td>{e(k.replace('_', ' '))}</td><td class=n>{v['auto_links']}</td><td class=n>{pct(v['precision'])}</td>"
                    f"<td class=n>{pct(v['recall'])}</td><td class=n>{v['sent_to_review']}</td></tr>" for k, v in mt.items())
    allr = m["detection"]["ALL"]
    page = f"""<!doctype html><html lang=en><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Leakage monitor - Northside Physio (synthetic)</title>
<style>:root{{--bg:#fff;--fg:#1c2330;--mut:#667;--line:#dde;--acc:#0b5fff}}
@media(prefers-color-scheme:dark){{:root{{--bg:#12161d;--fg:#e6e9ef;--mut:#9aa3b2;--line:#2a3140;--acc:#6ea0ff}}}}
body{{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;max-width:960px;margin:0 auto;padding:24px 16px}}
h1{{font-size:1.5rem;margin:0}}h2{{font-size:1.1rem;margin-top:2rem}}table{{border-collapse:collapse;width:100%}}
td,th{{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}}.n{{text-align:right;white-space:nowrap}}
.big{{font-size:2rem;color:var(--acc);font-weight:700}}.cards{{display:flex;gap:24px;flex-wrap:wrap;margin:16px 0}}small,.mut{{color:var(--mut)}}
.warn{{border:1px solid var(--line);padding:8px 12px;border-radius:6px}}</style>
<h1>Enquiry-to-cash leakage - Northside Physio</h1>
<p class=warn><b>Synthetic data.</b> The clinic, people and numbers are fictional. Every action below is a draft awaiting human approval; nothing is sent.</p>
<div class=cards><div><div class=big>{gbp(tot_h)}</div>hard &pound; at risk<br><small>invoices unpaid / never raised</small></div>
<div><div class=big>{gbp(tot_e)}</div>expected &pound; at risk<br><small>modelled from observed conversion; an estimate</small></div>
<div><div class=big>{len(leaks)}</div>leaks flagged<br><small>{pct(allr['recall'])} of planted found, {pct(allr['precision'])} precision</small></div></div>
<h2>&pound; at risk by leak point</h2>
<table><tr><th>Leak point<th class=n>Count<th class=n>Hard &pound;<th class=n>Expected &pound;<th class=n>Recall<th class=n>Precision</tr>{''.join(rows)}</table>
<h2>Top 10 actions by value</h2><table><tr><th>Leak<th class=n>Value<th>Drafted action</tr>{trs}</table>
<h2>Identity matching vs ground truth</h2>
<table><tr><th>Link<th class=n>Auto links<th class=n>Precision<th class=n>Recall<th class=n>To human review</tr>{mrows}</table>
<p class=mut>Low-confidence pairs (0.50-0.85) go to the Gemini stub, then to a human queue; {m['identity_review_queue']['appointments_withheld_pending_review']} appointments are withheld from invoicing alerts until identities are confirmed.
Valuation inputs: average patient value &pound;{m['params']['avg_patient_value_gbp']:,.0f}, conversion after a fast reply {pct(m['params']['conv_rate_fast_response'])},
high-intent {pct(m['params']['conv_rate_high_intent'])}, chase recovery factor {m['params']['recovery_factor']} (assumption).</p>
</html>"""
    out = Path(out) if out else d / "leakage_report.html"
    out.write_text(page)
    return out


if __name__ == "__main__":
    print(render())
