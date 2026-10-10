# 06: Data plan (public data only, real businesses, many of them)

## Decisions (from review, 2026-10-11)
- **Public data only.** No private records.
- **Real businesses, including large ones, and several of them:** Munshi works for a **portfolio of client businesses**, like a real CA firm.
- **The agent researches each business itself** (who they are, what they do, how they make money, what "normal" looks like for them) before touching their numbers.

## The honest constraint
Private businesses never publish their **transaction-level** books (bank lines, every bill). Companies *do* publish their **financial statements**, and real business **documents** (invoices, receipts) exist in public research datasets. So Munshi does two kinds of CA work, each on the right real data:

| CA job | Real data it runs on |
| --- | --- |
| **A. Research + financial review** *(peer benchmarks = SHOULD; full review mode = STRETCH)* of a business (the annual/quarterly CA review: do the numbers hold together, what's the tax picture, what's unusual, what should the owner be asked?) | **Real filed financials** of real companies: large US public companies (SEC EDGAR) and UK small/mid companies (Companies House) |
| **B. Month close** from documents (read bills/receipts, match to bank, balance to the rupee) | **Real business documents** (DocILE invoices, SROIE/CORD receipts) + a bank statement **generated from those documents** (labelled generated) |

## Sources
| Source | What it is | Access | Used for |
| --- | --- | --- | --- |
| **SEC EDGAR XBRL API** (`data.sec.gov/api/xbrl/companyfacts/CIK##########.json`, `submissions/`) | Every financial fact every US public company has filed (revenue, expenses, tax, cash, balance sheet), by period | Free, no key; descriptive User-Agent required; ≤10 req/s | Job A: large-company clients; peer benchmarks |
| **Companies House** (free API + accounts data product, iXBRL) | Filed accounts and company records of UK companies, including **small businesses** | Free API key; bulk accounts files (check current terms on day 1) | Job A: small/mid clients; company status, officers |
| **Crustdata** (5,000 credits) | Company + people + jobs data | API key | Research: what the business does, size, headcount, hiring; payee resolution in job B |
| **The business's own website / filings text** (10-K business section, annual report) | How they describe their business, revenue model, risks | Public web | Research: business model + tax profile |
| **DocILE** | 6,680 real annotated business documents (invoices) | Registration may be needed (check hour 1) | Job B documents |
| **SROIE / CORD** | Real scanned receipts with labels | Open (HF/Kaggle) | Job B documents |
| **Dodo test mode** | Real payments API | Test key | Invoices + payments in job B; our billing |

## Real businesses Munshi researches
**CORE/SHOULD (inside the one story):** for the demo business, Munshi picks **3–5 real peers** itself (same industry, similar size): US agencies/consultancies from **SEC EDGAR** and UK agencies from **Companies House** filed accounts. It uses their real figures to set expectations ("software spend 9% vs peers 4%").

**STRETCH (review mode):** a portfolio of 5–7 real companies (large US public companies incl. one with an unusual year; UK small companies) reviewed end to end, as in "job A" above.

## What "verification" means on real filings (deterministic, in code)
- Assets = Liabilities + Equity (every period).
- Net income reconciles from the income statement to the cash flow statement.
- Ending cash on the cash flow statement = cash on the balance sheet.
- Effective tax rate = tax expense ÷ pre-tax income; flag if far from the company's own history or from peers.
- Quarter-over-quarter / year-over-year jumps beyond thresholds → explain or ask.
- Any figure the agent cites is fetched from the filing data with its source tag (XBRL concept + period + filing id), never typed by the LLM.

## Job B: the month-close test month (Studio Kaveri)
- **60–80 real documents** (DocILE invoices, SROIE/CORD receipts), assigned to a fictional agency, clearly labelled.
- **Bank statement generated** from those documents + salaries, rent, transfers, in a common bank CSV export format.
- **Planted traps** (each one something a good CA catches):

| # | Trap | Tests |
| --- | --- | --- |
| 1 | Same bill uploaded twice | Dedup |
| 2 | Payment with no bill → not claimable yet | Matching + tax |
| 3 | One payment covering 3 invoices | One-to-many matching |
| 4 | Partial client payment | Collections |
| 5 | Vendor refund | Categorisation |
| 6 | Cryptic narration (`RZP*ACMETECH 88213`) | Payee resolution (Crustdata) |
| 7 | Blurry/rotated receipt | Recovery |
| 8 | Bill with a wrong total (vendor's error) | Verification |
| 9 | Un-invoiced work in the timesheet | Invoicing + Dodo |
| 10 | Invoice 38 days overdue | Collections |
| 11 | Entry posted twice → books off | Gap hunt |
| 12 | Personal expense on the business account | Owner-in-the-loop |

- **Answer key:** the correct ledger + expected categories, matches and open items, written alongside the generator.

## Answer keys for job A
For each real company, the "right answers" are **checkable facts**: the identities above, the reported tax expense and pre-tax income, and known events from the filing (e.g. a reported restatement or one-off charge). The scorer checks Munshi found the real anomalies and made no false claims.

## Privacy and honesty
- All data is public; no private individuals' data is used beyond published company officers' names where filings include them.
- Generated parts (Studio Kaveri's bank statement, timesheet) are labelled generated in the README and demo.
- neatlogs PII redaction on.
