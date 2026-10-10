"""Unpack the SROIE test split (361 real scanned receipts, CC BY 4.0) into images + answer labels.

Labels (company, date, address, total) are the benchmark answer key for Munshi's document reader.
"""

import ast
import json
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data/raw/datasets/sroie_test.parquet"
OUT = ROOT / "data/benchmark/sroie"


def main() -> None:
    (OUT / "images").mkdir(parents=True, exist_ok=True)
    labels = {}
    for row in pq.read_table(SRC).to_pylist():
        key = row["key"]
        (OUT / "images" / f"{key}.jpg").write_bytes(row["image"]["bytes"])
        ent = row["entities"]
        labels[key] = ent if isinstance(ent, dict) else ast.literal_eval(ent)
    (OUT / "labels.json").write_text(json.dumps(labels, indent=1, ensure_ascii=False), encoding="utf-8")
    (OUT / "SOURCE.md").write_text(
        "# SROIE benchmark\n\nReal scanned receipts from the ICDAR 2019 SROIE competition (test split, 361 receipts),\n"
        "via Hugging Face `jsdnrs/ICDAR2019-SROIE`, licence CC BY 4.0. `labels.json` holds the expert labels\n"
        "(company, date, address, total) used to score Munshi's document reader.\n",
        encoding="utf-8",
    )
    print(f"{len(labels)} receipts -> {OUT}")


if __name__ == "__main__":
    main()
