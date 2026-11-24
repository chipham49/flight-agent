# Comparison: v2 vs v3

| Metric | v2 | v3 | Change |
|---|---|---|---|
| cases | 8 | 8 | +0  |
| eval_limits | max 3 web searches, no retry | max 3 web searches, no retry |  |
| pass_rate | 87.5 | 100.0 | +12.5 ✅ |
| behaviour_accuracy | 100.0 | 100.0 | +0.0  |
| route_accuracy | 100.0 | 100.0 | +0.0  |
| results_with_offers | 100.0 | 100.0 | +0.0  |
| citation_rate | 100.0 | 100.0 | +0.0  |
| bag_fee_applied | 0.0 | 100.0 | +100.0 ✅ |
| price_verified_rate | 0.0 | 0.0 | +0.0  |
| offers_dropped_by_guardrails | 0 | 4 | +4 ✅ |
| total_cost_usd | 0.2034 | 0.1696 | -0.0338 ✅ |
| avg_cost_per_search_case | 0.0508 | 0.0423 | -0.0085 ✅ |
| median_seconds_search_case | 27.450000000000003 | 28.95 | +1.5 ⚠️ |
| max_seconds | 34.1 | 41.3 | +7.2 ⚠️ |

| Group | v2 | v3 |
|---|---|---|
| domestic | 1/1 | 1/1 |
| fees_rag | 0/1 | 1/1 |
| guardrail | 3/3 | 3/3 |
| international | 1/1 | 1/1 |
| memory | 1/1 | 1/1 |
| vague | 1/1 | 1/1 |

**Regression check:** passed ✅
