#!/usr/bin/env python3
"""Detect silences in the vol1 m4bs (paragraph pauses) for sync snapping.
Writes scratchpad/silences_v1_<voice>.json: [[midpoint_s, duration_s], ...]"""
import json, re, subprocess
from pathlib import Path

SP = Path('/private/tmp/claude-501/-Users-bryan-SteingrimurTranslation/f4cf9616-0683-4aa1-bce7-b7fba1acc523/scratchpad')
BOOKS = [
    ("v1_bryan", "Steingrimur_Vol1_Bryan_voice.m4b"),
    ("v1_stein", "Steingrimur_Vol1_Steingrimur_voice.m4b"),
    ("v1_johann", "Steingrimur_Vol1_Johann_voice.m4b"),
]

for tag, m4b in BOOKS:
    src = SP / "release_staging" / m4b
    p = subprocess.run(
        ["ffmpeg", "-v", "info", "-i", str(src),
         "-af", "silencedetect=noise=-35dB:d=0.25", "-f", "null", "-"],
        capture_output=True, text=True)
    sil = []
    start = None
    for m in re.finditer(r"silence_(start|end): ([\d.]+)(?: \| silence_duration: ([\d.]+))?", p.stderr):
        kind, t = m.group(1), float(m.group(2))
        if kind == "start": start = t
        elif start is not None:
            dur = float(m.group(3)) if m.group(3) else t - start
            sil.append([round((start + t) / 2, 2), round(dur, 3)])
            start = None
    (SP / f"silences_{tag}.json").write_text(json.dumps(sil))
    print(tag, len(sil), "silences", flush=True)
