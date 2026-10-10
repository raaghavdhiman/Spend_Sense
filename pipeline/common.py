import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(r"C:\Users\Raaghav\Desktop\FORGEHACKS\.env")
DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)

def env(name):
    v = os.getenv(name)
    if not v:
        raise SystemExit(f"Missing {name} in .env")
    return v