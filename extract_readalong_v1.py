#!/usr/bin/env python3
"""Vol-1 read-along manifests. The old vol-1 builds kept no per-paragraph
timings, but m4b chapter boundaries are exact — interpolate paragraph times
within each chapter proportional to text length. Output: public/ra/v1_*.json"""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
PROJECT = HERE.parent
SP = Path('/private/tmp/claude-501/-Users-bryan-SteingrimurTranslation/f4cf9616-0683-4aa1-bce7-b7fba1acc523/scratchpad')

sys.path.insert(0, str(PROJECT / "audiobook" / "inworld_test"))
SRC = PROJECT / "archive" / "Steingrimur_Vol1_English.md"
LINES = SRC.read_text(encoding="utf-8").split("\n")

SEGMENTS = [  # from build_vol1_bryan.py
    ("foreword",  76,  117,  "Foreword"),
    ("chapter1",  117, 626,  "Fragments of Memory from Childhood"),
    ("chapter2",  626, 1148, "The Years in the Prime Minister's Residence"),
    ("chapter3",  1148,1578, "Sturdy Boys, the War Years, and Girl Troubles"),
    ("chapter4",  1578,2138, "Student Years and Great Ambition"),
    ("chapter5",  2138,2792, "The Promised Land"),
    ("chapter6",  2792,3229, "Years of Enterprise in Iceland"),
    ("chapter7",  3229,3826, "Broken Hopes and the Later American Years"),
    ("chapter8",  3826,4483, "Divorce and the Battle for the Children"),
    ("chapter9",  4483,4902, "Research, Marriage, and Wrestling Bouts"),
    ("chapter10", 4902,5408, "A New Beginning"),
    ("epilogue",  5408,5436, "Epilogue"),
]

def clean(chunk):
    t = "\n".join(chunk)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", t)
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"\[p\.?\s*\d+\]", "", t)
    t = re.sub(r"\[\^\d+\]", "", t)
    out = []
    for ln in t.split("\n"):
        s = ln.strip()
        if not s: out.append(""); continue
        s = re.sub(r"^#+\s*", "", s); s = s.replace("*", "")
        out.append(s)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(out)).strip()

def paragraphs(start, end):
    text = clean(LINES[start-1:end-1])
    paras = [re.sub(r"^\s*>\s?", "", p.strip(), flags=re.M).replace("\n", " ").strip()
             for p in text.split("\n\n")]
    return [p for p in paras if p and re.search(r"[^\W\d_]", p)]

def main():
    chapters_all = json.loads((SP / "chapters.json").read_text())
    BOOKS = [
        ("v1_bryan", "Steingrimur_Vol1_Bryan_voice.m4b", 1),    # ch 0 = spoken intro, no text
        ("v1_stein", "Steingrimur_Vol1_Steingrimur_voice.m4b", 0),
        ("v1_johann", "Steingrimur_Vol1_Johann_voice.m4b", 0),
    ]
    outdir = HERE / "public" / "ra"; outdir.mkdir(exist_ok=True)
    for tag, m4b, ch_offset in BOOKS:
        chs = chapters_all[m4b]
        # chapter end = next chapter start (last: leave open, estimated below)
        units, chapters = [], []
        for i, (base, start, end, title) in enumerate(SEGMENTS):
            meta = chs[i + ch_offset]
            ch_start = meta["t"]
            ch_end = chs[i + ch_offset + 1]["t"] if i + ch_offset + 1 < len(chs) else None
            paras = paragraphs(start, end)
            total_chars = sum(len(p) + 80 for p in paras)  # +80 ≈ inter-paragraph pause weight
            if ch_end is None:  # estimate epilogue length from speech rate
                ch_end = ch_start + total_chars / 16.0
            dur = ch_end - ch_start
            t = ch_start
            for p_txt in paras:
                w = (len(p_txt) + 80) / total_chars * dur
                units.append({"c": base, "t": p_txt, "b": round(t, 2), "e": round(t + w, 2)})
                t += w
            chapters.append({"base": base, "label": meta["title"], "t": ch_start})
        out = {"audio": m4b, "approx": True, "chapters": chapters, "units": units}
        f = outdir / f"{tag}.json"
        f.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
        print(f"{tag}: {len(units)} units, {f.stat().st_size//1024} KB")

if __name__ == "__main__":
    main()
