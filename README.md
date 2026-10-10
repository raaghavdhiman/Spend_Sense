# SpendSense: an AI procurement copilot

SpendSense cleans messy purchase records, compares what each vendor charges for
the same item, shows the savings in rupees, and, once a buyer approves, sends the
vendor a request for quotation (RFQ) and reads the quote that comes back.

Built in 36 hours for the **AI + Business** hackathon: turn data into insights,
predictions and recommendations.

**Live demo (Momen preview):** https://ed09ok818wgle.cave.momenapp.com/

> **Note:** The Momen preview link is regenerated every 24 hours. If it doesn't
> load, the demo video above shows the full flow, and the link in this README
> is refreshed daily.

**Demo video:** https://youtu.be/Fa3l93o6TyI

## The problem
The same item is bought under many spellings ("A4 copier paper 75gsm 500 sht",
"Copier Paper A4 (500)", ...), from several vendors, at drifting prices. Nobody can
see that one vendor has quietly raised its price, so the money leaks.

## How it works
```
purchases.csv (messy)
   -> Featherless LLM extracts type / colour / pack size (controlled vocabulary)
   -> group identical items, compare average paid price per pack, per vendor
   -> ranked savings recommendations with evidence, in rupees
   -> loaded into Momen (database + app)
Buyer clicks Approve in the app
   -> Momen calls an n8n webhook
   -> n8n sends an RFQ email from the SpendSense inbox (Agentboxd)
Vendor replies (simulated by a bot)
   -> Featherless extracts price + lead time from the reply
   -> the quote is written back onto the card in Momen
```

## Tech stack
| Tool | Role |
|---|---|
| **Featherless AI** | Open-source LLM (Qwen3.8-27B) extracts item attributes and reads vendor quotes |
| **Momen** | Database, the Landing and Insights app, the Approve action |
| **n8n** | Approve -> RFQ email workflow (webhook -> HTTP request) |
| **Agentboxd** | Real inboxes for the SpendSense agent and the vendor; sends and reads email |
| Python | Pipeline: pandas, pydantic, requests, openai SDK |

## Results (controlled benchmark)
Synthetic data with savings planted on purpose, so accuracy can be measured:
- 204 purchase lines, 45 distinct descriptions, 9 real items, 4 vendors, 6 months
- 100% of lines grouped into the correct item
- 100% of the planted savings recovered: Rs 83,215 per quarter
- Every recommendation shows its evidence (average price per pack by vendor,
  number of purchase lines)

This is a benchmark on generated data, not a claim about production accuracy.

## Design choices
- **Controlled vocabulary.** The model may only choose from fixed lists for type
  and colour, and answers outside the list are rejected, so spelling variants
  cannot create duplicate items.
- **Weighted averages.** Price per pack is total rupees / total packs, not a
  simple average of prices.
- **Human in the loop.** Nothing is emailed until the buyer approves.
- **Untrusted email is treated as data.** Vendor replies flagged by Agentboxd's
  checks are skipped, and the extraction prompt ignores instructions inside them.

## Run the pipeline
```
pip install -r requirements.txt
copy .env.example .env          # then fill in your keys
cd pipeline
py 1_generate_data.py           # synthetic purchases + ground truth
py 2_extract.py                 # LLM extraction (cached, resumable)
py 3_analyze.py                 # grouping, comparison, savings, actions.csv
py 4_load_momen.py              # wipe + load the Momen `actions` table
py 5_vendor_bot.py              # simulated vendor (own terminal, start first)
py 6_quote_reader.py            # reads quotes back into Momen (own terminal)
```
Momen `actions` table: id, item_name, vendor, best_vendor, est_savings_inr (BigInt),
recommendations, evidence, status, quote (all Text except the BigInt).

`n8n/spendsense-rfq.json` is the exported workflow. Import it into n8n, add a Header
Auth credential for Agentboxd, and publish it.

Replace YOUR-WEBHOOK-ID and YOUR-SPENDSENSE-INBOX-ID in the workflow with your own values.

## Limitations
- Data is synthetic and the vendor is a bot.
- No login: the prototype's Momen permissions are open.
- The card shows a vendor quote after a page reload, because the quote is written
  from outside Momen.
- The Momen app is a preview link and could expire.
