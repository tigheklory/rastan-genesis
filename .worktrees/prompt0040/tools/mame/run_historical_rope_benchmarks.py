#!/usr/bin/env python3
"""Batch the existing deterministic Genesis NTSC rope benchmark over ROM history."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "tools/mame/run_rope_attach_performance_benchmark.sh"
LUA = ROOT / "tools/mame/scripts/rope_attach_performance_benchmark.lua"
SUMMARIZER = ROOT / "tools/mame/summarize_rope_attach_benchmark.py"
DEFAULT_OUTPUT = ROOT / "states/traces/historical_rope_benchmark"
ARCADE_FRAMES = 771
ARCADE_MS = 12850.000

MODERN_RE = re.compile(r"rastan_direct_video_test_build_(\d{4})\.bin$")
FULL_HUD_RE = re.compile(r"rastan_direct_video_test_build_(\d{4})_full_hud\.bin$")
LEGACY_RE = re.compile(r"Rastan_(\d+)\.bin$")

KNOWN: dict[int, tuple[int, float | None]] = {
    419: (878, 14652.200),
    422: (879, 14668.888),
    423: (858, 14318.437),
    424: (817, 13634.222),
    425: (817, None),
    426: (806, 13450.653),
    428: (803, 13400.588),
    433: (803, 13400.588),
    435: (803, 13400.588),
}
KNOWN_FULL_HUD: dict[int, tuple[int, float | None]] = {435: (854, 14251.684)}


@dataclass(frozen=True)
class Artifact:
    dataset: str
    build: int
    path: Path
    sha256: str


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def benchmark_identity() -> str:
    digest = hashlib.sha256()
    for path in (RUNNER, LUA, SUMMARIZER):
        digest.update(path.relative_to(ROOT).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def discover() -> dict[str, dict[int, Artifact]]:
    found: dict[str, dict[int, Path]] = {"canonical": {}, "full-hud": {}}
    modern_root = ROOT / "dist/rastan-direct"
    for path in sorted(modern_root.glob("*.bin")):
        if match := MODERN_RE.fullmatch(path.name):
            found["canonical"][int(match.group(1))] = path
        elif match := FULL_HUD_RE.fullmatch(path.name):
            found["full-hud"][int(match.group(1))] = path

    # Exact legacy canonical names are supported only when the modern artifact
    # for that build is absent. Suffixed diagnostics are deliberately excluded.
    for path in sorted((ROOT / "dist/Old").glob("Rastan_*.bin")):
        if match := LEGACY_RE.fullmatch(path.name):
            found["canonical"].setdefault(int(match.group(1)), path)

    return {
        dataset: {
            build: Artifact(dataset, build, path, sha256_file(path))
            for build, path in paths.items()
        }
        for dataset, paths in found.items()
    }


def parse_builds(value: str | None) -> set[int] | None:
    if not value:
        return None
    result: set[int] = set()
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            first, last = (int(item) for item in part.split("-", 1))
            if last < first:
                raise argparse.ArgumentTypeError(f"descending build range: {part}")
            result.update(range(first, last + 1))
        else:
            result.add(int(part))
    return result


def read_cache(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return list(data.get("records", []))


def recover_run_records(output_root: Path) -> list[dict[str, Any]]:
    """Recover completed per-ROM records after an interrupted batch."""
    records: list[dict[str, Any]] = []
    for path in sorted((output_root / "runs").glob("**/batch_result.json")):
        try:
            record = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(record, dict) and all(
            field in record
            for field in (
                "dataset", "build", "rom_sha256", "benchmark_identity",
                "trials_requested", "max_frames", "measured_at_utc",
            )
        ):
            records.append(record)
    return records


def record_key(record: dict[str, Any]) -> tuple[Any, ...]:
    return (
        record["dataset"],
        record["build"],
        record["rom_sha256"],
        record["benchmark_identity"],
        record["trials_requested"],
        record["max_frames"],
    )


def parse_trial_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="") as source:
        return list(csv.DictReader(source, delimiter="\t"))


def classify_failure(
    returncode: int | None,
    timed_out: bool,
    rows: list[dict[str, str]],
    diagnostic: str,
) -> tuple[str, str]:
    if rows:
        reasons = {row.get("reason", "") for row in rows}
        if "frame_budget_exhausted" in reasons:
            started = any(int(row.get("start_frame", "-1")) >= 0 for row in rows)
            return ("NO_ROPE" if started else "NO_GAMEPLAY", "frame_budget_exhausted")
    if timed_out or returncode == 124:
        return "TIMEOUT", "bounded invocation timeout"
    lower = diagnostic.lower()
    crash_markers = (
        "address error",
        "illegal instruction",
        "bus error",
        "fatal error",
        "genesis crash",
        "lock up real hardware",
    )
    if any(marker in lower for marker in crash_markers):
        return "CRASH", "obvious crash signature in benchmark output"
    return "BENCHMARK_ERROR", f"runner exit {returncode} without a complete result"


def run_one(
    artifact: Artifact,
    trials: int,
    identity: str,
    output_root: Path,
    timeout_seconds: int,
    max_frames: int,
) -> dict[str, Any]:
    build_tag = f"{artifact.build:04d}" + ("_full_hud" if artifact.dataset == "full-hud" else "")
    run_dir = (
        output_root
        / "runs"
        / artifact.dataset
        / f"build_{artifact.build:04d}"
        / f"trials_{trials}"
        / artifact.sha256[:16]
    )
    run_dir.mkdir(parents=True, exist_ok=True)
    command = [str(RUNNER), str(artifact.path), build_tag, str(trials), str(run_dir)]
    env = os.environ.copy()
    env["ROPE_BENCH_MAX_FRAMES"] = str(max_frames)
    timed_out = False
    returncode: int | None = None
    stdout = ""
    stderr = ""
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        returncode = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as error:
        timed_out = True
        stdout = error.stdout or ""
        stderr = error.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="replace")

    (run_dir / "batch_runner_stdout.txt").write_text(stdout)
    (run_dir / "batch_runner_stderr.txt").write_text(stderr)
    rows = parse_trial_rows(run_dir / "trials.tsv")
    passed = returncode == 0 and len(rows) == trials and all(row.get("result") == "PASS" for row in rows)

    frames: list[int] = []
    milliseconds: list[float] = []
    if passed:
        frames = [int(row["elapsed_frames"]) for row in rows]
        milliseconds = [float(row["elapsed_milliseconds"]) for row in rows]
        status, note = "PASS", ""
    else:
        diagnostic_parts = [stdout, stderr]
        for path in sorted(run_dir.glob("trial_*/mame_stderr.txt")):
            diagnostic_parts.append(path.read_text(errors="replace"))
        for path in sorted(run_dir.glob("trial_*/mame_stdout.txt")):
            diagnostic_parts.append(path.read_text(errors="replace"))
        status, note = classify_failure(returncode, timed_out, rows, "\n".join(diagnostic_parts))

    record: dict[str, Any] = {
        "dataset": artifact.dataset,
        "build": artifact.build,
        "rom_path": artifact.path.relative_to(ROOT).as_posix(),
        "rom_sha256": artifact.sha256,
        "benchmark_identity": identity,
        "trials_requested": trials,
        "max_frames": max_frames,
        "status": status,
        "trial_frames": frames,
        "trial_milliseconds": milliseconds,
        "median_frames": statistics.median(frames) if frames else None,
        "median_milliseconds": statistics.median(milliseconds) if milliseconds else None,
        "deterministic": "YES" if frames and len(set(frames)) == 1 else ("NO" if frames else "N/A"),
        "note": note,
        "returncode": returncode,
        "timed_out": timed_out,
        "result_dir": run_dir.relative_to(ROOT).as_posix(),
        "measured_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "batch_result.json").write_text(json.dumps(record, indent=2) + "\n")
    return record


def selected_result(
    artifact: Artifact, records: list[dict[str, Any]], identity: str, max_frames: int
) -> dict[str, Any] | None:
    matches = [
        record
        for record in records
        if record["dataset"] == artifact.dataset
        and record["build"] == artifact.build
        and record["rom_sha256"] == artifact.sha256
        and record["benchmark_identity"] == identity
        and record["max_frames"] == max_frames
    ]
    if not matches:
        return None
    return max(matches, key=lambda item: (item["trials_requested"], item["measured_at_utc"]))


def fmt_number(value: float | int | None, decimals: int = 3) -> str:
    if value is None:
        return ""
    if isinstance(value, int) or float(value).is_integer():
        return str(int(value))
    return f"{float(value):.{decimals}f}"


def decorate_results(
    dataset: str,
    artifacts: dict[int, Artifact],
    records: list[dict[str, Any]],
    identity: str,
    max_frames: int,
) -> list[dict[str, Any]]:
    if not artifacts:
        return []
    builds = sorted(artifacts)
    if dataset == "canonical":
        builds = list(range(min(builds), max(builds) + 1))
    output: list[dict[str, Any]] = []
    previous_pass: dict[str, Any] | None = None
    known = KNOWN if dataset == "canonical" else KNOWN_FULL_HUD
    for build in builds:
        artifact = artifacts.get(build)
        if artifact is None:
            row: dict[str, Any] = {
                "dataset": dataset,
                "build": build,
                "rom_path": "",
                "rom_sha256": "",
                "trials_requested": 0,
                "status": "MISSING_ARTIFACT",
                "trial_frames": [],
                "trial_milliseconds": [],
                "median_frames": None,
                "median_milliseconds": None,
                "deterministic": "N/A",
                "note": "no canonical numbered ROM artifact found",
            }
        else:
            cached = selected_result(artifact, records, identity, max_frames)
            if cached is None:
                row = {
                    "dataset": dataset,
                    "build": build,
                    "rom_path": artifact.path.relative_to(ROOT).as_posix(),
                    "rom_sha256": artifact.sha256,
                    "trials_requested": 0,
                    "status": "NOT_RUN",
                    "trial_frames": [],
                    "trial_milliseconds": [],
                    "median_frames": None,
                    "median_milliseconds": None,
                    "deterministic": "N/A",
                    "note": "artifact discovered but no current cached result",
                }
            else:
                row = dict(cached)

        frames = row.get("median_frames")
        milliseconds = row.get("median_milliseconds")
        row["delta_frames_vs_previous"] = None
        row["delta_ms_vs_previous"] = None
        row["delta_frames_vs_arcade"] = None
        row["delta_ms_vs_arcade"] = None
        row["percent_vs_arcade"] = None
        if row["status"] == "PASS" and frames is not None and milliseconds is not None:
            if previous_pass is not None:
                row["delta_frames_vs_previous"] = frames - previous_pass["median_frames"]
                row["delta_ms_vs_previous"] = milliseconds - previous_pass["median_milliseconds"]
            row["delta_frames_vs_arcade"] = frames - ARCADE_FRAMES
            row["delta_ms_vs_arcade"] = milliseconds - ARCADE_MS
            row["percent_vs_arcade"] = (milliseconds - ARCADE_MS) / ARCADE_MS * 100.0
            previous_pass = row

            expected = known.get(build)
            if expected:
                discrepancies = []
                if frames != expected[0]:
                    discrepancies.append(f"known frames {expected[0]}")
                if expected[1] is not None and abs(milliseconds - expected[1]) > 0.001:
                    discrepancies.append(f"known ms {expected[1]:.3f}")
                if discrepancies:
                    detail = "KNOWN_VALUE_DISCREPANCY: " + ", ".join(discrepancies)
                    row["note"] = "; ".join(filter(None, (row.get("note", ""), detail)))
        output.append(row)
    return output


def write_dataset(output_root: Path, dataset: str, rows: list[dict[str, Any]], identity: str) -> None:
    stem = "canonical" if dataset == "canonical" else "full_hud"
    fields = [
        "build", "rom_path", "rom_sha256", "trials_requested", "trial_frames",
        "median_frames", "trial_milliseconds", "median_milliseconds", "deterministic",
        "delta_frames_vs_previous", "delta_ms_vs_previous", "delta_frames_vs_arcade",
        "delta_ms_vs_arcade", "percent_vs_arcade", "status", "note",
    ]
    with (output_root / f"{stem}_results.csv").open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            cooked = dict(row)
            cooked["trial_frames"] = ";".join(str(value) for value in row.get("trial_frames", []))
            cooked["trial_milliseconds"] = ";".join(
                f"{value:.3f}" for value in row.get("trial_milliseconds", [])
            )
            for field in (
                "median_milliseconds", "delta_ms_vs_previous", "delta_ms_vs_arcade",
                "percent_vs_arcade",
            ):
                cooked[field] = fmt_number(cooked.get(field))
            writer.writerow(cooked)
    payload = {
        "dataset": dataset,
        "platform": "GENESIS NTSC MAME",
        "arcade_silver_standard": {"frames": ARCADE_FRAMES, "milliseconds": ARCADE_MS},
        "benchmark_identity": identity,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "results": rows,
    }
    (output_root / f"{stem}_results.json").write_text(json.dumps(payload, indent=2) + "\n")


def write_summary(output_root: Path, datasets: dict[str, list[dict[str, Any]]]) -> None:
    lines = [
        "# Historical deterministic rope benchmark",
        "",
        "Platform: **GENESIS NTSC MAME**. Existing gameplay route and timing semantics are unchanged.",
        f"Arcade silver standard: **{ARCADE_FRAMES} frames / {ARCADE_MS:.3f} ms**.",
        "",
    ]
    for dataset, rows in datasets.items():
        title = "Canonical" if dataset == "canonical" else "Full HUD"
        lines.extend([
            f"## {title}",
            "",
            "| Build | Status | Frames | Time ms | Delta from previous | Delta from arcade | % vs arcade | Notes |",
            "|---:|---|---:|---:|---:|---:|---:|---|",
        ])
        for row in rows:
            prev = ""
            if row.get("delta_frames_vs_previous") is not None:
                prev = f"{row['delta_frames_vs_previous']:+g} fr / {row['delta_ms_vs_previous']:+.3f} ms"
            arcade = ""
            percent = ""
            if row.get("delta_frames_vs_arcade") is not None:
                arcade = f"{row['delta_frames_vs_arcade']:+g} fr / {row['delta_ms_vs_arcade']:+.3f} ms"
                percent = f"{row['percent_vs_arcade']:+.3f}%"
            note = row.get("note", "")
            if row.get("delta_frames_vs_previous") is not None and abs(row["delta_frames_vs_previous"]) >= 5:
                note = "; ".join(filter(None, (note, "PERFORMANCE_STEP_CHANGE")))
            lines.append(
                f"| {row['build']:04d} | {row['status']} | {fmt_number(row.get('median_frames'))} | "
                f"{fmt_number(row.get('median_milliseconds'))} | {prev} | {arcade} | {percent} | {note} |"
            )
        lines.append("")
    lines.extend([
        "Performance step labels identify measured changes only; they do not attribute causes.",
        "",
    ])
    (output_root / "summary.md").write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=("canonical", "full-hud", "both"), default="both")
    parser.add_argument("--trials", type=int, choices=(1, 3), default=1)
    parser.add_argument("--builds", help="comma-separated builds and inclusive ranges")
    parser.add_argument("--min-build", type=int)
    parser.add_argument("--max-build", type=int)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=int, default=200)
    parser.add_argument("--max-frames", type=int, default=12000)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--resume", action="store_true", help="explicit name for default cache behavior")
    parser.add_argument(
        "--confirm-passes",
        action="store_true",
        help="run only artifacts having a cached PASS for this benchmark identity",
    )
    parser.add_argument("--force", action="store_true", help="rerun matching cached results")
    args = parser.parse_args()
    if args.jobs < 1 or args.timeout_seconds < 1 or args.max_frames < 1:
        parser.error("jobs, timeout-seconds, and max-frames must be positive")

    output_root = args.output.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    identity = benchmark_identity()
    artifacts = discover()
    selected_datasets = ("canonical", "full-hud") if args.dataset == "both" else (args.dataset,)
    requested_builds = parse_builds(args.builds)
    cache_path = output_root / "cache.json"
    records = read_cache(cache_path) + recover_run_records(output_root)
    cache_by_key = {record_key(record): record for record in records}

    queue: list[Artifact] = []
    for dataset in selected_datasets:
        for build, artifact in sorted(artifacts[dataset].items()):
            if requested_builds is not None and build not in requested_builds:
                continue
            if args.min_build is not None and build < args.min_build:
                continue
            if args.max_build is not None and build > args.max_build:
                continue
            if args.confirm_passes and not any(
                record["dataset"] == dataset
                and record["build"] == build
                and record["rom_sha256"] == artifact.sha256
                and record["benchmark_identity"] == identity
                and record["max_frames"] == args.max_frames
                and record["status"] == "PASS"
                for record in records
            ):
                continue
            key = (dataset, build, artifact.sha256, identity, args.trials, args.max_frames)
            if not args.force and key in cache_by_key:
                print(f"CACHE {dataset} {build:04d} {cache_by_key[key]['status']}")
            else:
                queue.append(artifact)

    if queue:
        print(f"Running {len(queue)} artifact(s), {args.trials} trial(s) each, jobs={args.jobs}")
        with ThreadPoolExecutor(max_workers=args.jobs) as executor:
            futures = {
                executor.submit(
                    run_one, artifact, args.trials, identity, output_root,
                    args.timeout_seconds, args.max_frames,
                ): artifact
                for artifact in queue
            }
            for future in as_completed(futures):
                artifact = futures[future]
                try:
                    record = future.result()
                except Exception as error:  # keep the rest of a long sweep alive
                    print(f"ERROR {artifact.dataset} {artifact.build:04d}: {error}", file=sys.stderr)
                    continue
                cache_by_key[record_key(record)] = record
                print(
                    f"{record['status']} {artifact.dataset} {artifact.build:04d} "
                    f"frames={record['trial_frames']}"
                )

    records = sorted(
        cache_by_key.values(),
        key=lambda item: (item["dataset"], item["build"], item["trials_requested"], item["measured_at_utc"]),
    )
    cache_path.write_text(json.dumps({"records": records}, indent=2) + "\n")

    decorated: dict[str, list[dict[str, Any]]] = {}
    for dataset in ("canonical", "full-hud"):
        decorated[dataset] = decorate_results(dataset, artifacts[dataset], records, identity, args.max_frames)
        write_dataset(output_root, dataset, decorated[dataset], identity)
    write_summary(output_root, decorated)
    print(f"Results: {output_root.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
