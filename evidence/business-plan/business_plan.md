# Munshi: business plan

**Built from measured usage**: the model tokens of the traced v2 evidence close (`runs/evidence/close-v2/run.json`),
priced at public list prices (assumption). The neatlogs dashboard shows the actual cost per traced close.

## Unit economics (per customer per month)
| Item | ₹ |
| --- | --- |
| LLM cost of the demo close (measured tokens × list price) | 1.39 |
| LLM cost scaled ×3 for a real business month (assumption) | 4.17 |
| Crustdata lookups (cached) | 8.00 |
| Infra share | 40.00 |
| **COGS per customer** | **52.17** |
| ARPU (70% Solo ₹999, 30% Business ₹2,999) | 1,599.00 |
| Payment / merchant-of-record fee (Dodo, 4%) | 63.96 |
| **Gross margin** | **92.7%** |

Model usage detail: `{"claude-haiku": {"calls": 18, "prompt": 4958, "completion": 1623, "usd": 0.0131}, "claude-sonnet-4.6": {"calls": 1, "prompt": 371, "completion": 146, "usd": 0.0033}, "nova-lite": {"calls": 2, "prompt": 1909, "completion": 267, "usd": 0.0002}}`

## Pricing
Solo ₹999/month (1 business, 150 documents) · Business ₹2,999/month (600 documents, invoicing + collections) ·
₹5 per extra document (Dodo usage meter). Billed through Dodo Payments as merchant of record.

## Scenarios (18 months, starting cash ₹1,500,000)
Fixed costs ₹153,000/month: founder stipends (2) ₹120,000, tools & hosting base ₹8,000, marketing ₹25,000.
| Scenario | Start customers | Monthly growth | Break-even month | Customers at month 18 | Cash at month 18 |
| --- | --- | --- | --- | --- | --- |
| Base | 20 | 15% | 13 | 215 | ₹995,107 |
| Growth | 40 | 25% | 6 | 1,776 | ₹11,679,257 |

Full month-by-month table: `business_plan_inputs.csv`.
