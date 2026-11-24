# Comparison: v1 vs v2

| Metric | v1 | v2 | Change |
|---|---|---|---|
| cases | 8 | 8 | +0  |
| eval_limits | max 3 web searches, no retry | max 3 web searches, no retry |  |
| pass_rate | 75.0 | 87.5 | +12.5 ✅ |
| behaviour_accuracy | 75.0 | 100.0 | +25.0 ✅ |
| route_accuracy | 75.0 | 100.0 | +25.0 ✅ |
| results_with_offers | 50.0 | 100.0 | +50.0 ✅ |
| citation_rate | 50.0 | 100.0 | +50.0 ✅ |
| bag_fee_applied | 0.0 | 0.0 | +0.0  |
| price_verified_rate | 0.0 | 0.0 | +0.0  |
| offers_dropped_by_guardrails | 0 | 0 | +0  |
| total_cost_usd | 0.1281 | 0.2034 | +0.0753 ⚠️ |
| avg_cost_per_search_case | 0.0319 | 0.0508 | +0.0189 ⚠️ |
| median_seconds_search_case | 18.25 | 27.450000000000003 | +9.2 ⚠️ |
| max_seconds | 24.7 | 34.1 | +9.4 ⚠️ |

| Group | v1 | v2 |
|---|---|---|
| domestic | 1/1 | 1/1 |
| fees_rag | 0/1 | 0/1 |
| guardrail | 3/3 | 3/3 |
| international | 1/1 | 1/1 |
| memory | 0/1 | 1/1 |
| vague | 1/1 | 1/1 |

**Regression check:** passed ✅
