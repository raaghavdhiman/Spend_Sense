# Makes data/purchases.csv (what the company bought, messy) and data/truth.csv (answer key)
import csv, random
from common import DATA

random.seed(7)  # same data every run, so your demo numbers never change

PEN_BLUE = ["Ball pen blue 0.7mm box of 50", "Ballpoint pens, blue, 0.7 mm, pack 50",
            "BLUE BALL PEN 0.7 (50 PCS BOX)", "Pen ballpoint blue 0.7mm 50pk",
            "Blue ball point pen 0.7 box/50"]
def to_black(s):
    return s.replace("blue", "black").replace("Blue", "Black").replace("BLUE", "BLACK")

# item_id: (base price per pack in INR, (min qty, max qty) per order, 5 messy spellings)
ITEMS = {
    "paper": (285, (20, 80), ["A4 Paper 75GSM Ream 500 sheets", "Copier paper A4 75 gsm (500 shts)",
              "A4 75gsm photocopy paper ream", "PAPER A4 75 GSM 500S", "A4 size copy paper 75g 1 ream"]),
    "pen_blue": (260, (10, 40), PEN_BLUE),
    "pen_black": (255, (10, 40), [to_black(s) for s in PEN_BLUE]),
    "folder": (410, (5, 20), ["File folder A4 plastic blue pack of 25", "Plastic folders A4 blue 25 pcs",
              "A4 PLASTIC FILE FOLDER BLUE 25PK", "Folder file A4 plastic (blue) x25",
              "Blue plastic file folders A4 - 25 pack"]),
    "sticky": (180, (10, 40), ["Sticky notes 3x3 inch yellow 12 pads", "Post-it style notes 3 x 3 in yellow pack 12",
              "YELLOW STICKY NOTE PAD 3X3 (12 PADS)", "Sticky pad 3x3in yellow 12pk",
              "Yellow sticky notes 3x3 inch - set of 12"]),
    "marker": (220, (5, 25), ["Whiteboard marker black bullet tip box of 10", "White board markers, black, bullet, 10 pcs",
              "BLACK WHITEBOARD MARKER BULLET TIP 10PK", "Marker whiteboard blk bullet 10 pack",
              "Black bullet-tip whiteboard markers x10"]),
    "notebook": (330, (10, 50), ["Notebook A5 ruled 200 pages pack of 6", "A5 ruled notebooks 200 pg (6 pcs)",
              "RULED NOTEBOOK A5 200 PAGES 6PK", "Note book A5 lined 200pgs set of 6", "A5 200-page ruled notebook x6"]),
    "highlighter": (150, (5, 25), ["Highlighter yellow chisel tip pack of 10", "Yellow highlighters, chisel, 10 pcs",
              "HIGHLIGHTER PEN YELLOW CHISEL 10PK", "Hi-lighter yellow chisel tip 10 pack", "Yellow chisel highlighter x10"]),
    "toner": (2400, (2, 8), ["Toner cartridge 12A compatible black", "Compatible toner 12A black 1 pc",
              "TONER CART 12A BLACK COMPATIBLE", "Black toner, 12A, compatible", "12A compatible black toner cartridge"]),
}
VENDORS = {"OfficeMart": 1.00, "StationeryHub": 1.18, "PaperPlus": 0.93, "BulkBazaar": 1.04}
MONTHS = ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]

rows = []
for item_id, (base, (qmin, qmax), spellings) in ITEMS.items():
    for vendor, factor in VENDORS.items():
        for i, month in enumerate(MONTHS):
            for _ in range(random.choice([0, 1, 1, 2])):          # 0-2 orders per month
                creep = 1 + 0.025 * i if vendor == "BulkBazaar" else 1   # planted price creep
                price = round(base * factor * creep * random.uniform(0.97, 1.03))
                qty = random.randint(qmin, qmax)
                rows.append({"date": f"{month}-15", "vendor": vendor,
                             "description": random.choice(spellings),   # each order spelled differently
                             "qty": qty, "unit_price": price, "total": qty * price, "item_id": item_id})

rows.sort(key=lambda r: r["date"])
for n, r in enumerate(rows, 1):
    r["line_id"] = n

cols = ["line_id", "date", "vendor", "description", "qty", "unit_price", "total"]
with open(DATA / "purchases.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
with open(DATA / "truth.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=["line_id", "item_id"], extrasaction="ignore"); w.writeheader(); w.writerows(rows)
print(f"{len(rows)} purchase lines written")