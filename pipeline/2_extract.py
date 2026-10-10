# Messy text -> structured fields, using Featherless. Saves answers to data/extracted.json
import csv, json, os
from openai import OpenAI
from pydantic import BaseModel, field_validator
from common import DATA, env

TYPES = ["copier paper", "ballpoint pen", "file folder", "sticky notes",
         "whiteboard marker", "notebook", "highlighter", "toner cartridge"]
COLOURS = ["white", "blue", "black", "yellow", "red", "green", "none"]
MODEL = os.getenv("FEATHERLESS_MODEL", "Qwen/Qwen3.8-27B")

SYSTEM = (
    "You convert ONE messy office-stationery purchase description into ONE JSON object. "
    "Output ONLY the JSON object, no explanation.\n"
    "Fields:\n"
    '- "type": exactly one of ' + json.dumps(TYPES) + "\n"
    '- "spec": short key size/spec in lowercase, e.g. "a4 75gsm", "0.7mm", "3x3in". Empty string if none.\n'
    '- "colour": one of ' + json.dumps(COLOURS) + '. Use a colour ONLY if the text states it, otherwise "none". Never guess.\n'
    '- "pack_qty": integer, how many units are in the pack as bought. A ream = 500; "box of 50" = 50; a single item = 1.\n'
    "Examples:\n"
    "Input: Ball pen red 1.0mm 20 pcs\n"
    'Output: {"type":"ballpoint pen","spec":"1.0mm","colour":"red","pack_qty":20}\n'
    "Input: A3 COPY PAPER 80GSM 1 REAM\n"
    'Output: {"type":"copier paper","spec":"a3 80gsm","colour":"none","pack_qty":500}\n'
    "Input: Yellow highlighter fine tip 4pk\n"
    'Output: {"type":"highlighter","spec":"fine tip","colour":"yellow","pack_qty":4}\n'
)

class Extracted(BaseModel):
    type: str
    spec: str
    colour: str
    pack_qty: int

    @field_validator("type")
    @classmethod
    def check_type(cls, v):
        v = v.strip().lower()
        if v not in TYPES:
            raise ValueError(f"type not in list: {v}")
        return v

    @field_validator("colour")
    @classmethod
    def check_colour(cls, v):
        v = v.strip().lower()
        if v not in COLOURS:
            raise ValueError(f"colour not in list: {v}")
        return v

client = OpenAI(base_url="https://api.featherless.ai/v1", api_key=env("FEATHERLESS_API_KEY"))

def ask(desc):
    err = None
    for _ in range(2):                                   # one retry if the answer is invalid
        r = client.chat.completions.create(model=MODEL, temperature=0, messages=[
            {"role": "system", "content": SYSTEM}, {"role": "user", "content": desc}])
        text = r.choices[0].message.content
        try:
            blob = text[text.index("{"): text.rindex("}") + 1]   # ignore any chatter around the JSON
            return Extracted.model_validate_json(blob).model_dump()
        except Exception as e:
            err = e
    print("FAILED:", desc, "->", err)
    return None

cache_file = DATA / "extracted.json"
cache = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}

with open(DATA / "purchases.csv", encoding="utf-8") as f:
    unique = sorted({row["description"] for row in csv.DictReader(f)})   # ask once per unique text
todo = [d for d in unique if cache.get(d) is None]
print(f"{len(unique)} unique descriptions, {len(todo)} to extract")

for i, desc in enumerate(todo, 1):
    cache[desc] = ask(desc)
    cache_file.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")  # save after each call
    print(f"{i}/{len(todo)}  {desc}  ->  {cache[desc]}")