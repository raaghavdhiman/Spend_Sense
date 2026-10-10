# Plays the vendor: answers every RFQ with a quote. Start it BEFORE you click Approve.
import csv, random, re, threading
from agentboxd import Agentboxd
from common import DATA, env

VENDOR_INBOX = env("AGENTBOXD_VENDOR_INBOX_ID")
SS_ADDRESS = env("AGENTBOXD_SPENDSENSE_ADDRESS")

# cheapest average price per item = the first price in each action's evidence text
BEST_PRICE = {}
with open(DATA / "actions.csv", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        m = re.search(r"(?:₹|Rs)\s?([\d,]+)", row["evidence"])
        if m:
            BEST_PRICE[row["item_name"]] = int(m.group(1).replace(",", ""))

TEMPLATES = [
    "Hello,\n\nThank you for your enquiry. Our quotation for {item}: Rs {price} per pack, "
    "delivery in {days} days. Valid for 7 days.\n\nRegards,\nSales desk",
    "Hi team, we can offer {item} at Rs {price} per pack with a {days}-day lead time. "
    "The offer holds for a week. - Sales desk",
    "Dear buyer, quote for {item}: INR {price} / pack. Lead time approx. {days} days. "
    "Terms: 30 days credit.",
]

mr = Agentboxd()

def item_from_subject(subject):
    # "Re: RFQ: Item name"  ->  "Item name"   (also handles "RFQ [#29]: Item name")
    return re.sub(r"^(re:\s*)*rfq\s*(\[#\d+\])?\s*:?\s*", "", subject, flags=re.I).strip()

def handle(msg):
    subject = msg.get("subject") or ""
    if SS_ADDRESS not in (msg.get("from") or "") or "rfq" not in subject.lower():
        return                                   # not an RFQ from SpendSense: ignore it
    item = item_from_subject(subject)
    base = BEST_PRICE.get(item)
    if base is None:
        print("WARNING: unknown item, using a made-up price:", item)
        base = 250
    price = round(base * random.uniform(0.94, 0.99))   # a bit below today's best price
    days = random.randint(3, 7)
    text = random.choice(TEMPLATES).format(item=item, price=price, days=days)
    mr.messages.reply(VENDOR_INBOX, msg["id"], text=text)
    print(f"Quoted Rs {price} for: {item}")

if __name__ == "__main__":
    stop = threading.Event()
    print("Vendor bot is listening (Ctrl+C to stop)...")
    try:
        mr.inboxes.consume(VENDOR_INBOX, handle, stop=stop)
    except KeyboardInterrupt:
        stop.set()