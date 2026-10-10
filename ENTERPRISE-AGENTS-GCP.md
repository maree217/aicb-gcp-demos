# How UK banks are building agents on GCP (Oct 2026)

Compiled from public sources; items marked unverified need checking. Interpretation, not advice.

## Per-org table

| Organisation | What is public |
|---|---|
| Lloyds | Vertex ML platform; 18+ GenAI systems; Envoy agent marketplace (source: cityam.com, Apr 2026); Athena (unverified) |
| HSBC | Google + DeepMind partnership, Jun 2026; AML AI |
| NatWest | FCA live test of an agentic complaints handler with human-in-the-loop; cloud not stated |
| Starling | Gemini assistant, in production |
| Deutsche Bank | Gemini Enterprise for Financial Services design partner, preview |
| Dojo | Chargeback agent; 680+ employee-built agents |
| Barclays | Claude, not GCP |

## Recurring work types, ranked

1. Agent platform / marketplace
2. Staff assistants
3. Governance and eval
4. Fin-crime
5. ML platform migration
6. Customer assistants

## Regulatory frame

- PRA SS1/23: effective May 2024, amended Apr 2026.
- Google Cloud designated a critical third party, Jul 2026.
- FCA AI Live Testing.
- Mills Review, via a law-firm summary.

## Gemini Enterprise Agent Platform component status

| Component | Status |
|---|---|
| Workflow Builder | GA 3 Sep 2026 |
| Agent Registry | GA 25 Jun 2026 |
| Agent identity | GA 25 Jun 2026 |
| A2A registration | GA 17 Aug 2026 |
| FS Financial Research agent | Preview |

## Claude on Vertex

- Listed for London and the EU multi-region; verify each model.
- Multi-region GA 15 May 2026.
- The global endpoint has no residency guarantee.
- ADK via LiteLlm.
- No verified bank customer story.

## Six prototype shapes

See [arch-5](arch-5-prototype-shapes.png). Sample repos:

- https://github.com/google/adk-samples
- https://github.com/GoogleCloudPlatform/agent-starter-pack
- https://github.com/a2aproject/a2a-samples

## Sources

- googlecloudpresscorner.com/2026-08-25-Google-Cloud-Launches-Gemini-Enterprise-for-Financial-Services
- hsbc.com HSBC/Google release 2026
- lloydsbankinggroup.com 9 Apr 2025 release
- cityam.com/exclusive-lloyds-in-tie-up-with-google-to-build-ai-agents/
- natwestgroup.com FCA testing May 2026
- starlingbank.com agentic assistant
- cloud.google.com/transform/financial-services-ai-agents-gemini-enterprise-round-up
- cloud.google.com/blog multi-region-endpoints-for-claude
- docs.cloud.google.com/gemini/enterprise/docs/release-notes

Compiled from public sources; items marked unverified need checking. Interpretation, not advice.
