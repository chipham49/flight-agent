# Comparison: v1 vs v3

| Metric | v1 | v3 | Change |
|---|---|---|---|
| cases | 8 | 8 | +0  |
| eval_limits | max 3 web searches, no retry | max 3 web searches, no retry |  |
| pass_rate | 75.0 | 100.0 | +25.0 ✅ |
| behaviour_accuracy | 75.0 | 100.0 | +25.0 ✅ |
| route_accuracy | 75.0 | 100.0 | +25.0 ✅ |
| results_with_offers | 50.0 | 100.0 | +50.0 ✅ |
| citation_rate | 50.0 | 100.0 | +50.0 ✅ |
| bag_fee_applied | 0.0 | 100.0 | +100.0 ✅ |
| price_verified_rate | 0.0 | 0.0 | +0.0  |
| offers_dropped_by_guardrails | 0 | 4 | +4 ✅ |
| total_cost_usd | 0.1281 | 0.1696 | +0.0415 ⚠️ |
| avg_cost_per_search_case | 0.0319 | 0.0423 | +0.0104 ⚠️ |
| median_seconds_search_case | 18.25 | 28.95 | +10.7 ⚠️ |
| max_seconds | 24.7 | 41.3 | +16.6 ⚠️ |

| Group | v1 | v3 |
|---|---|---|
| domestic | 1/1 | 1/1 |
| fees_rag | 0/1 | 1/1 |
| guardrail | 3/3 | 3/3 |
| international | 1/1 | 1/1 |
| memory | 0/1 | 1/1 |
| vague | 1/1 | 1/1 |

**Regression check:** passed ✅
