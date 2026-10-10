# Leakage demo (synthetic): Northside Physio

Runnable proof of Build G in `gcp-enterprise-ai-capability-map.md`. The clinic, people, emails and phones are all fictional (example.* domains, Ofcom drama-range numbers). Stdlib only, no network, no GCP, no spend.

```
python3 leakage_generate.py     # seeded 12 months -> leakage_data_{gmail,cliniko,xero,truth}.json
python3 leakage_pipeline.py     # normalise, match, detect, value, draft -> leakage_data_{leaks,actions,metrics}.json
python3 leakage_report.py       # -> leakage_report.html (open in a browser)
python3 -m pytest -q leakage_test_pipeline.py
```

Files: `leakage_generate.py` (data + planted leaks + ground truth), `leakage_pipeline.py` (the engine; `match_with_gemini()` is the stub where Vertex Gemini resolves 0.50-0.85 confidence pairs), `leakage_report.py` (static HTML), `leakage_test_pipeline.py`.
Generated `leakage_data_*.json` is gitignored; `leakage_report.html` is committed.

Caveats: the ground truth is built from the same rules the detector uses, so recall near 100% proves the plumbing and the matching, not real-world accuracy. Expected-GBP figures (leaks 1-3) are modelled estimates (conversion x average patient value, chase recovery factor 0.3 is an assumption); leaks 4-5 are hard invoice amounts. Every drafted action has status "awaiting approval"; nothing is sent.
