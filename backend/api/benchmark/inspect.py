"""Print per-question ranks and latency from the latest benchmark result.

Run with: uv run python -m benchmark.inspect   (from backend/api)
"""

import json
from pathlib import Path

RESULTS_DIR = Path(__file__).parent / "results"

latest = sorted(RESULTS_DIR.glob("*.json"))[-1]
data = json.loads(latest.read_text(encoding="utf-8"))

print(f"{latest.name}\n")

for r in sorted(data["answerable"], key=lambda r: r["rank"] or 999):
    print(f"rank {r['rank']:>2}  {r['id']:<10} {r['question']}")

print("\n--- unanswerable ---")
for r in data["unanswerable"]:
    print(f"\n{r['id']}: {r['question']}")
    for item in r["retrieved"][:3]:
        print(f"    {item['heading']}")

print("\n--- latency ---")
rows = data["answerable"] + data["unanswerable"]
searches = sorted(r["timings"]["search_ms"] for r in rows)
embeds = sorted(r["timings"]["embed_ms"] for r in rows)

print(f"search_ms  min {searches[0]}  median {searches[len(searches) // 2]}  max {searches[-1]}")
print(f"  all: {searches}")
print(f"embed_ms   min {embeds[0]}  median {embeds[len(embeds) // 2]}  max {embeds[-1]}")
