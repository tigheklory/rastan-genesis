#!/usr/bin/env python3
"""Write build metadata header for the Rastan launcher."""

from __future__ import annotations

import argparse
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Write apps/rastan build info header.")
    parser.add_argument("--header", required=True, help="Path to build_info.h")
    parser.add_argument("--build-number", required=True, type=int)
    parser.add_argument("--build-stamp", required=True)
    parser.add_argument("--variant", required=True)
    parser.add_argument("--hook-mode", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    header_path = Path(args.header)
    header_path.parent.mkdir(parents=True, exist_ok=True)
    hook_suffix = "N" if "nohook" in args.hook_mode else "H"
    build_line = f"WORLD REV1 BASELINE UI {args.build_number} {hook_suffix}"

    contents = f"""#ifndef RASTAN_BUILD_INFO_H
#define RASTAN_BUILD_INFO_H

#define RASTAN_BUILD_NUMBER {args.build_number}
#define RASTAN_BUILD_STAMP "{args.build_stamp}"
#define RASTAN_BUILD_VARIANT "{args.variant}"
#define RASTAN_BUILD_HOOK_MODE "{args.hook_mode}"
#define RASTAN_BUILD_LINE "{build_line}"

#endif
"""

    header_path.write_text(contents, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
