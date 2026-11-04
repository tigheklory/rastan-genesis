#!/usr/bin/env bash
# Focused read-only Build-0532 capture for the minimal-jumping stale 8-pixel row.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export R1S2_0532_TRACE_ROOT="${ROOT}/states/traces/r1s2_minimal_jump_stale_row_build_0532"
export R1S2_0532_TRACE_ROUTE="minimal_jumping_only"
export R1S2_0532_TRACE_INSTRUCTION="Use only the three ordinary jumps required to grab the first three chains. Do not repeatedly jump against a wall. Press M as soon as the full-width stale 8-pixel strip appears, keep playing for about one second, then close MAME."

echo "Focused minimal-jumping R1-S2 stale-row trace"
echo "Important: ignore narrow four-tile surface changes; mark only the full-width stale strip."
exec "${ROOT}/tools/diagnostics/run_r1s2_build0532_remaining_trace.sh" "$@"
