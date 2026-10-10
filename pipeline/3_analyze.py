# Group same items, compare vendor prices, estimate savings, write data/actions.csv, print accuracy
import json
import pandas as pd
from common import DATA

P = pd.read_csv(DATA / "purchases.csv")
ext = json.loads((DATA / "extracted.json").read_text(encoding="utf-8"))

# 1) attach the extracted fields to every purchase line
P["fields"] = P["description"].map(ext)
unmatched = int(P["fields"].isna().sum())
P = P.dropna(subset=["fields"]).copy()
P = P.join(pd.DataFrame(list(P["fields"]), index=P.index))
P["month"] = P["date"].str[:7]
months = sorted(P["month"].unique())

# 2) "same item" = same type + colour + pack size
P["key"] = P["type"] + "|" + P["colour"] + "|" + P["pack_qty"].astype(str)

def savings_6m(g):
    """What was overpaid vs the cheapest vendor's average price (over all 6 months)."""
    s = g.groupby("vendor")[["total", "qty"]].sum()
    avg = s["total"] / s["qty"]                      # weighted average price per vendor
    others = g[g["vendor"] != avg.idxmin()]
    return ((others["unit_price"] - avg.min()).clip(lower=0) * others["qty"]).sum()

rows = []
for key, g in P.groupby("key"):
    s = g.groupby("vendor")[["total", "qty"]].sum()
    avg = s["total"] / s["qty"]
    best, best_avg = avg.idxmin(), avg.min()
    others = g[g["vendor"] != best]
    over = others.groupby("vendor").apply(
        lambda x: ((x["unit_price"] - best_avg).clip(lower=0) * x["qty"]).sum())
    current = over.idxmax()                          # vendor you overpay the most with                   # vendor you spend the most with today
    est = int(round(savings_6m(g) / 2))              # 6 months of data -> per quarter
    gap = (avg.max() / best_avg - 1) * 100

    cg = g[g["vendor"] == current]                   # simple trend: current vendor, early vs late months
    early, late = cg[cg["month"].isin(months[:2])], cg[cg["month"].isin(months[-2:])]
    trend = None
    if len(early) and len(late):
        trend = (late.total.sum() / late.qty.sum()) / (early.total.sum() / early.qty.sum()) * 100 - 100

    t, colour, pack = key.split("|")
    name = t.title() + f" {g['spec'].mode()[0]}".rstrip()
    name += "" if colour == "none" else f", {colour}"
    name += "" if pack == "1" else f" (pack of {pack})"

    rec = f"Buy from {best} (avg ₹{best_avg:,.0f} per pack). You paid up to {gap:.0f}% more at other vendors."
    if trend is not None and trend > 5:
        rec += f" {current} has raised its price {trend:.0f}% since {pd.Timestamp(months[0] + '-01').strftime('%B')}."
    evidence = ", ".join(f"{v} ₹{p:,.0f}" for v, p in avg.sort_values().items())
    evidence += f" (average paid per pack, {len(g)} purchase lines)"
    rows.append({"item_name": name, "vendor": current, "best_vendor": best, "est_savings_inr": est,
                 "recommendations": rec, "evidence": evidence, "status": "pending"})

actions = pd.DataFrame(rows)
actions = actions[actions["est_savings_inr"] > 0].sort_values("est_savings_inr", ascending=False)
actions.to_csv(DATA / "actions.csv", index=False, encoding="utf-8")

# 3) accuracy against the answer key
T = P.merge(pd.read_csv(DATA / "truth.csv"), on="line_id")
majority = T.groupby("item_id")["key"].agg(lambda s: s.mode()[0])
T["ok"] = T["key"] == T["item_id"].map(majority)
found = P.groupby("key").apply(savings_6m).sum() / 2
planted = T.groupby("item_id").apply(savings_6m).sum() / 2
print(f"Item groups found: {P['key'].nunique()} (expected {T['item_id'].nunique()})")
print(f"Lines grouped correctly: {T['ok'].mean() * 100:.1f}%   (lines with no extraction: {unmatched})")
print(f"Savings found: Rs {found:,.0f} per quarter vs planted Rs {planted:,.0f}  ({found / planted * 100:.0f}%)")
print(f"Actions written: {len(actions)}")
bad = T[~T["ok"]][["description", "key"]].drop_duplicates().head(10)
if len(bad):
    print("Mismatches to look at:"); print(bad.to_string())