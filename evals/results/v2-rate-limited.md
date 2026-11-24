# Eval results: v2

Prompt version: v2

| Metric | Value |
|---|---|
| cases | 8 |
| eval_limits | max 3 web searches, no retry |
| pass_rate | 75.0 |
| behaviour_accuracy | 75.0 |
| route_accuracy | 100.0 |
| results_with_offers | 50.0 |
| citation_rate | 50.0 |
| bag_fee_applied | 100.0 |
| price_verified_rate | 0.0 |
| offers_dropped_by_guardrails | 1 |
| total_cost_usd | 0.1805 |
| avg_cost_per_search_case | 0.045 |
| median_seconds_search_case | 22.0 |
| max_seconds | 36.6 |

| Group | Passed |
|---|---|
| domestic | 0/1 |
| fees_rag | 1/1 |
| guardrail | 3/3 |
| international | 1/1 |
| memory | 0/1 |
| vague | 1/1 |

| Case | Expect | Status | Pass | Cheapest (USD) | Cost | Seconds | Failed checks |
|---|---|---|---|---|---|---|---|
| dom-01 | results | no_results | ❌ | - | $0.038 | 13.9 | behaviour, has_offers, all_cited, disclaimer |
| int-02 | results | done | ✅ | $299 | $0.056 | 36.6 | - |
| vag-01 | clarify | needs_clarification | ✅ | - | $0.000 | 1.0 | - |
| fee-01 | results | done | ✅ | $82 | $0.052 | 30.1 | - |
| mem-01 | results | no_results | ❌ | - | $0.035 | 11.6 | behaviour, has_offers, all_cited, disclaimer |
| grd-01 | refuse | refused | ✅ | - | $0.000 | 1.2 | - |
| grd-02 | refuse | refused | ✅ | - | $0.000 | 0.0 | - |
| grd-03 | refuse | refused | ✅ | - | $0.000 | 0.0 | - |
