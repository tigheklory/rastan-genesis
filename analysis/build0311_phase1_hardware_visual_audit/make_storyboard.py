#!/usr/bin/env python3
"""Build deterministic metadata and a filterable HTML index for the Build 0311 capture."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


DENSE_WINDOWS = {
    "gameplay_entry": (17.500, 3.000, None, None, "transition"),
    "section02_record01_descent": (27.250, 17.250, 2, 1, "vertical"),
    "section02_record01_exit": (46.500, 4.000, 2, 1, "transition"),
    "vertical_transition_01": (56.500, 17.000, None, None, "vertical"),
    "mid_phase_transition_01": (89.000, 12.000, None, None, "transition"),
    "mid_phase_transition_02": (117.000, 12.000, None, None, "transition"),
    "late_phase_transition_01": (145.000, 12.000, None, None, "transition"),
    "late_phase_transition_02": (175.000, 12.000, None, None, "transition"),
    "fortress_approach": (202.000, 12.000, None, None, "horizontal"),
}


def probe(video: Path) -> dict:
    raw = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration,size:stream=index,codec_type,avg_frame_rate,nb_frames",
        "-of", "json", str(video),
    ])
    return json.loads(raw)


def ratio(value: str) -> float:
    numerator, denominator = value.split("/", 1)
    return float(numerator) / float(denominator)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--audit-dir", required=True, type=Path)
    parser.add_argument("--sample-rate", required=True, type=float)
    args = parser.parse_args()

    info = probe(args.video)
    video_stream = next(s for s in info["streams"] if s["codec_type"] == "video")
    video_duration = float(info["format"]["duration"])
    source_frames = int(video_stream.get("nb_frames") or 0)
    source_fps = source_frames / video_duration if source_frames else ratio(video_stream["avg_frame_rate"])
    frames = sorted((args.audit_dir / "frames" / "baseline").glob("frame_*.jpg"))

    metadata = []
    for index, frame in enumerate(frames):
        timestamp = index / args.sample_rate
        metadata.append({
            "id": frame.stem,
            "path": str(frame.relative_to(args.audit_dir)),
            "timestamp_seconds": round(timestamp, 3),
            "timestamp": f"{int(timestamp // 60):02d}:{timestamp % 60:06.3f}",
            "approx_source_frame": round(timestamp * source_fps),
            "round": 1,
            "phase": 1,
            "section": None,
            "record": None,
            "epoch": None,
            "scroll_x": None,
            "scroll_y": None,
            "scroll_mode": "unknown",
            "selector": None,
            "classification": "UNCERTAIN",
            "issue_tags": [],
            "notes": "",
        })

    dense_metadata = []
    for window, (start, window_duration, section, record, mode) in DENSE_WINDOWS.items():
        window_frames = sorted((args.audit_dir / "frames" / "dense" / window).glob("frame_*.jpg"))
        for index, frame in enumerate(window_frames):
            timestamp = start + index / 12
            dense_metadata.append({
                "id": f"dense_{window}_{frame.stem}",
                "path": str(frame.relative_to(args.audit_dir)),
                "window": window,
                "timestamp_seconds": round(timestamp, 3),
                "timestamp": f"{int(timestamp // 60):02d}:{timestamp % 60:06.3f}",
                "approx_source_frame": round(timestamp * source_fps),
                "round": 1,
                "phase": 1,
                "section": section,
                "record": record,
                "epoch": None,
                "scroll_x": None,
                "scroll_y": None,
                "scroll_mode": mode,
                "selector": 0 if section == 2 else None,
                "classification": "WRONG" if section == 2 and timestamp >= 27.75 else "UNCERTAIN",
                "issue_tags": ["wrong-plane-a-palette"] if section == 2 and timestamp >= 27.75 else [],
                "notes": "Dense transition evidence; unmeasured state remains null.",
            })

    metadata_dir = args.audit_dir / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    (metadata_dir / "frames.json").write_text(json.dumps(metadata, indent=2) + "\n")
    (metadata_dir / "dense_frames.json").write_text(json.dumps(dense_metadata, indent=2) + "\n")
    summary = {
        "source": str(args.video),
        "duration_seconds": video_duration,
        "source_frames": source_frames,
        "source_fps_derived": source_fps,
        "baseline_sample_rate_fps": args.sample_rate,
        "baseline_selected_frames": len(metadata),
        "dense_sample_rate_fps": 12,
        "dense_selected_frames": len(dense_metadata),
        "dense_windows": [
            {"name": name, "start_seconds": values[0], "duration_seconds": values[1]}
            for name, values in DENSE_WINDOWS.items()
        ],
    }
    (metadata_dir / "capture.json").write_text(json.dumps(summary, indent=2) + "\n")
    issues_path = args.audit_dir / "issues.json"
    if not issues_path.exists():
        issues_path.write_text("[]\n")

    cards = []
    for item in metadata + dense_metadata:
        section = str(item["section"]) if item["section"] is not None else "unknown"
        record = str(item["record"]) if item["record"] is not None else "pending"
        tags = " ".join(item["issue_tags"])
        cards.append(
            f'<article class="card" data-section="{section}" data-record="{record}" '
            f'data-mode="{item["scroll_mode"]}" data-class="{item["classification"]}" data-tags="{tags}">'
            f'<img loading="lazy" src="{item["path"]}" alt="{item["id"]}">'
            f'<div><b>{item["timestamp"]}</b> · source frame ~{item["approx_source_frame"]}</div>'
            f'<div>Section {section} · record {record} · {item["scroll_mode"]} · '
            f'{item["classification"]}</div></article>'
        )
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Build 0311 Round-1 Phase-1 Hardware Storyboard</title>
<style>
:root{{--paper:#efe8da;--ink:#211c17;--accent:#a9341f;--line:#c7b89d}}
body{{margin:0;background:var(--paper);color:var(--ink);font:15px Georgia,serif}}
header{{position:sticky;top:0;z-index:2;padding:14px 20px;background:#211c17;color:#fff;border-bottom:5px solid var(--accent)}}
h1{{font-size:22px;margin:0 0 8px}} .controls{{display:flex;gap:10px;flex-wrap:wrap}}
select,input{{font:inherit;padding:5px;background:#fff;border:1px solid var(--line)}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px;padding:16px}}
.card{{background:#fff;border:1px solid var(--line);box-shadow:3px 3px 0 #d9cdb9;padding:8px}}
.card img{{width:100%;height:auto;display:block;background:#000;margin-bottom:7px}}
.card.hide{{display:none}} small{{opacity:.8}}
</style></head><body>
<header><h1>Build 0311 · Round 1 Phase 1 · Real Genesis Hardware</h1>
<small>Complete 4-fps baseline plus bounded 12-fps transition windows. Hardware frames are visual/semantic locators only; MAME and arcade evidence are not frame-synchronized. <a href="comparison.html" style="color:#ffe0a8">Section-2 comparison</a> · <a href="metadata/section_audit.json" style="color:#ffe0a8">four-way section audit</a> · <a href="issues.json" style="color:#ffe0a8">issues and superseded history</a></small>
<div class="controls"><select id="section"><option value="all">All sections</option></select>
<select id="mode"><option value="all">All scroll modes</option><option>horizontal</option><option>vertical</option><option>transition</option><option>unknown</option></select>
<select id="klass"><option value="all">All classifications</option><option>CORRECT</option><option>WRONG</option><option>UNCERTAIN</option></select>
<input id="tag" placeholder="issue tag"></div></header>
<main>{''.join(cards)}</main>
<script>
const cards=[...document.querySelectorAll('.card')], sec=document.querySelector('#section');
for(let i=1;i<=16;i++)sec.insertAdjacentHTML('beforeend',`<option value="${{i}}">Section ${{i}}</option>`);
function filter(){{const s=sec.value,m=mode.value,k=klass.value,t=tag.value.toLowerCase();for(const c of cards){{c.classList.toggle('hide',!((s==='all'||c.dataset.section===s)&&(m==='all'||c.dataset.mode===m)&&(k==='all'||c.dataset.class===k)&&(!t||c.dataset.tags.includes(t))))}}}}
for(const el of document.querySelectorAll('select,input'))el.addEventListener('input',filter);
</script></body></html>"""
    (args.audit_dir / "index.html").write_text(html)


if __name__ == "__main__":
    main()
