#!/usr/bin/env python3
"""Refine vol1 read-along sync: snap estimated paragraph boundaries to real
audio silences (monotone, windowed). Rewrites public/ra/v1_*.json."""
import json
from pathlib import Path

HERE = Path(__file__).parent
SP = Path('/private/tmp/claude-501/-Users-bryan-SteingrimurTranslation/f4cf9616-0683-4aa1-bce7-b7fba1acc523/scratchpad')
WINDOW = 3.5      # seconds each side to search for a matching pause
MIN_STEP = 0.8    # boundaries must stay at least this far apart

def refine(tag):
    mf = HERE / "public" / "ra" / f"{tag}.json"
    data = json.loads(mf.read_text())
    sil = json.loads((SP / f"silences_{tag}.json").read_text())
    times = [s[0] for s in sil]
    import bisect
    moved = total = 0
    units = data["units"]
    # per chapter: snap internal boundaries (chapter anchors stay exact)
    for ci, ch in enumerate(data["chapters"]):
        idx = [i for i, u in enumerate(units) if u["c"] == ch["base"]]
        if len(idx) < 2: continue
        floor = units[idx[0]]["b"] + MIN_STEP
        for k in range(len(idx) - 1):
            i, j = idx[k], idx[k + 1]
            est = units[j]["b"]
            lo = bisect.bisect_left(times, max(est - WINDOW, floor))
            hi = bisect.bisect_right(times, est + WINDOW)
            best, best_score = None, -1e9
            for s in range(lo, hi):
                mid, dur = sil[s]
                if mid < floor: continue
                score = dur - 0.35 * abs(mid - est)
                if score > best_score: best_score, best = score, mid
            total += 1
            if best is not None and abs(best - est) > 0.05:
                units[i]["e"] = round(best, 2)
                units[j]["b"] = round(best, 2)
                moved += 1
                floor = best + MIN_STEP
            else:
                floor = est + MIN_STEP
    mf.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    print(f"{tag}: snapped {moved}/{total} boundaries")

for tag in ("v1_bryan", "v1_stein", "v1_johann"):
    refine(tag)
