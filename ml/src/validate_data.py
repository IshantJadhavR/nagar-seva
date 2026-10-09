# -*- coding: utf-8 -*-
"""Checks every CSV in ml/data for mistakes. Run:  python ml/src/validate_data.py"""
import re, sys
from pathlib import Path
import pandas as pd

DATA = Path(__file__).resolve().parents[1] / "data"
CATS = {"Roads", "Garbage", "Water Supply", "Drainage", "Streetlight", "Public Health", "Encroachment", "Other"}
DEV = re.compile(r"[\u0900-\u097F]")
problems = 0

def check(name, cond, msg):
    global problems
    if not cond:
        problems += 1
        print(f"  [PROBLEM] {name}: {msg}")

frames = {}
for f in ["complaints_train.csv", "complaints_test.csv", "complaints_external_test.csv", "complaints_external_pool.csv"]:
    df = pd.read_csv(DATA / f, encoding="utf-8-sig", keep_default_na=False)
    frames[f] = df
    print(f"\n{f}: {len(df)} rows")
    check(f, {"text", "language", "category"} <= set(df.columns), "missing columns")
    check(f, set(df.category) <= CATS, f"bad categories {set(df.category) - CATS}")
    check(f, set(df.language) <= {"English", "Hindi"}, "bad language values")
    sec = df.secondary_category[df.secondary_category != ""]
    check(f, set(sec) <= CATS, "bad secondary categories")
    has_dev = df.text.apply(lambda t: bool(DEV.search(t)))
    check(f, not ((df.language == "Hindi") & ~has_dev).any(), "Hindi rows without Devanagari")
    check(f, not ((df.language == "English") & has_dev).any(), "English rows with Devanagari")
    check(f, df.text.duplicated().sum() == 0, f"{df.text.duplicated().sum()} duplicate texts")
    check(f, (df.text.str.strip() != "").all(), "empty texts")
    print(pd.crosstab(df.category, df.language).to_string())

# leakage: test files must never overlap with training data
train_texts = set(frames["complaints_train.csv"].text) | set(frames["complaints_external_pool.csv"].text)
for t in ["complaints_test.csv", "complaints_external_test.csv"]:
    overlap = len(set(frames[t].text) & train_texts)
    check(t, overlap == 0, f"{overlap} texts also appear in training data (LEAKAGE)")
    print(f"\n{t} overlap with training data: {overlap}")

print("\nRESULT:", "ALL CHECKS PASSED" if problems == 0 else f"{problems} PROBLEM(S) FOUND")
sys.exit(1 if problems else 0)
