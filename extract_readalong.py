#!/usr/bin/env python3
"""Extract web read-along manifests from the vol2 fixed-layout epubs.
Output: public/ra/v2_<voice>.json with units (text + m4b-absolute times)."""
import json, re, zipfile
from pathlib import Path

HERE = Path(__file__).parent
PROJECT = HERE.parent
SP = Path('/private/tmp/claude-501/-Users-bryan-SteingrimurTranslation/f4cf9616-0683-4aa1-bce7-b7fba1acc523/scratchpad')

BOOKS = [
    ("v2_bryan", "Steingrimur_Vol2_ReadAlong_Bryan.epub",
     "Steingrimur_Vol2_Bryan_voice.m4b", "vol2_bryan_chapters.json"),
    ("v2_stein", "Steingrimur_Vol2_ReadAlong_Steingrimur.epub",
     "Steingrimur_Vol2_Steingrimur_voice.m4b", "vol2_stein_chapters.json"),
    ("v2_narr", "Steingrimur_Vol2_ReadAlong_Narrator.epub",
     "Steingrimur_Vol2_Narrator_voice.m4b", "vol2_narr_chapters.json"),
]
CHAPTER_ORDER = [f"chapter{i}" for i in range(1, 13)] + ["epilogue"]

def clock_to_s(c):
    h, m, s = c.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)

def main():
    outdir = HERE / "public" / "ra"; outdir.mkdir(exist_ok=True)
    for tag, epub, m4b, chjson in BOOKS:
        chapters_meta = json.loads((SP / chjson).read_text())
        offsets = {base: chapters_meta[i]["t"] for i, base in enumerate(CHAPTER_ORDER)}
        labels = {base: chapters_meta[i]["title"] for i, base in enumerate(CHAPTER_ORDER)}
        src = PROJECT / epub
        if not src.exists(): src = SP / "release_staging" / epub
        z = zipfile.ZipFile(src)
        names = z.namelist()
        smils = sorted(n for n in names if n.endswith(".smil"))
        units, texts = [], {}
        for smil in smils:
            page = smil.replace(".smil", ".xhtml")
            if page not in texts and page in names:
                xh = z.read(page).decode("utf-8")
                texts[page] = dict(re.findall(r'<span id="(u\d+)">(.*?)</span>', xh, re.S))
            body = z.read(smil).decode("utf-8")
            for m in re.finditer(
                r'<par[^>]*><text src="[^"#]*#(u\d+)"/><audio src="audio/([a-z0-9]+)\.m4a" '
                r'clipBegin="([\d:.]+)" clipEnd="([\d:.]+)"/></par>', body):

                uid, base, cb, ce = m.groups()
                if base not in offsets:  # intro etc. — not in the released m4b
                    continue
                t = texts.get(page, {}).get(uid, "")
                t = re.sub(r"<[^>]+>", "", t).strip()
                if not t: continue
                off = offsets[base]
                units.append({"c": base, "t": t,
                              "b": round(off + clock_to_s(cb), 2),
                              "e": round(off + clock_to_s(ce), 2)})
        chapters = [{"base": b, "label": labels[b], "t": offsets[b]} for b in CHAPTER_ORDER]
        out = {"audio": m4b, "chapters": chapters, "units": units}
        f = outdir / f"{tag}.json"
        f.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
        print(f"{tag}: {len(units)} units, {f.stat().st_size//1024} KB")

if __name__ == "__main__":
    main()
