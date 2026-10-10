# 08: Business model

## Customer and buyer
- **First customer:** owners of small service businesses (2–50 people) who do their own books or rely on a once-a-month accountant.
- **Second customer:** accounting / CA firms: one Munshi per client; the accountant reviews and signs instead of re-typing.

## Value (why they pay)
| For the owner | For the CA firm |
| --- | --- |
| Books always up to date, without data entry | Clients' months arrive closed, explained and balanced |
| Invoices go out on time; money arrives sooner (Dodo links + reminders) | More clients per accountant |
| No lost claims: missing bills chased the same month | Audit trail for every entry (books as code) |
| Tax set aside monthly: no year-end surprise | Fewer errors to fix |
| A CFO view on real numbers (via cfo.ai) | |

## Pricing (hypothesis, to be modelled in cfo.ai)
| Plan | Price | Includes |
| --- | --- | --- |
| **Solo** | ₹999 / month | 1 business, up to 150 documents/month |
| **Business** | ₹2,999 / month | Up to 600 documents, invoicing + collections |
| **Usage** | ₹5 per extra document | Metered via **Dodo Meters / Usage Events** |
| **CA firm** | per client per month | Volume pricing |
Billed through **Dodo** (subscriptions + usage), with Dodo as merchant of record.

## Unit economics: from real measurements, not guesses
```
Cost per close (per business per month) =
    LLM cost per close            ← neatlogs analytics (real, per end-user)
  + Crustdata cost                ← lookups per close × price
  + infra share                   ← AWS / hosting
  + payment fees                  ← Dodo rate on our revenue
```
The **neatlogs end-user cost** feeds the **cfo.ai** model directly. That's the meaningful bridge between the two sponsors: **our pricing is built on measured cost, not vibes.**

### cfo.ai model contents (the required business plan)
- Revenue: customers by plan × price + usage
- COGS: cost per close (neatlogs) × customers; Dodo fees
- Opex: team (2–3 founders), hosting, marketing
- Scenarios: **50 / 500 / 5,000 businesses**; a "price −30%" scenario; a "model cost halves" scenario
- Outputs: gross margin, break-even point, runway on a hypothetical seed round

## Go-to-market
1. **Founders like us:** the one-person and small-team companies building with AI (TheVibeFounder's audience). Launch on X during neatHack.
2. **CA firms:** one firm onboarding 20 clients is 20 customers; the books-as-code audit trail is their selling point.
3. **Integrations:** cfo.ai (books feed the CFO), Dodo (merchants already billing through Dodo get their books closed automatically).

## Competition and our angle
| Alternative | Gap Munshi fills |
| --- | --- |
| Doing it yourself in a spreadsheet | Time, errors, no audit trail |
| A human accountant (monthly/yearly) | Slow feedback, works from chaos, costly per hour |
| Accounting software (QuickBooks, Xero, Zoho Books, Tally) | Still needs someone to enter, match and categorise; Munshi is the **agent that does the work**, and can feed these tools |
| Bookkeeping services | Human-priced; Munshi is software-priced, with every decision explained |

**Our angle in one line:** *not another accounting app to fill in: an accountant that does the work and proves every number.*

## Risks to the business (for the pitch's honesty)
- Trust: mitigated by the evidence-first design and owner approval for every outgoing action.
- Liability: Munshi prepares; a human signs filings.
- Country tax differences: the tax engine is configurable; launch with one country profile.
