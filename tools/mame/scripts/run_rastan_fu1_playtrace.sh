#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
CMD_FILE="${REPO_ROOT}/tools/mame/scripts/rastan_fu1_playtrace_debug.cmd"
ROM_PATH="${REPO_ROOT}/roms"
ROM_ZIP="${ROM_PATH}/rastan.zip"
OUT_BASE_DEFAULT="${REPO_ROOT}/states/traces"

usage() {
  cat <<'USAGE'
Usage:
  run_rastan_fu1_playtrace.sh [--output-dir <path>]

Environment (optional):
  FU1_SECONDS_TO_RUN   If set, passes -seconds_to_run to MAME (smoke tests).
  FU1_QT_PLATFORM      If set, exported as QT_QPA_PLATFORM for MAME/debugger.
  FU1_MAME_EXTRA_ARGS  Extra MAME args appended to command line (smoke tests).
USAGE
}

OUT_DIR=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-dir)
      shift
      if [[ $# -eq 0 ]]; then
        echo "ERROR: --output-dir requires a value" >&2
        usage
        exit 1
      fi
      OUT_DIR="$1"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if ! command -v mame >/dev/null 2>&1; then
  echo "STOP: mame executable not found in PATH." >&2
  exit 1
fi

if [[ ! -f "${ROM_ZIP}" ]]; then
  echo "STOP: arcade ROM not found at ${ROM_ZIP}" >&2
  exit 1
fi

if [[ ! -f "${CMD_FILE}" ]]; then
  echo "STOP: debugger command file not found at ${CMD_FILE}" >&2
  exit 1
fi

if [[ -z "${OUT_DIR}" ]]; then
  TS="$(date +%Y%m%d_%H%M%S)"
  OUT_DIR="${OUT_BASE_DEFAULT}/fu1_rastan_playtrace_${TS}"
fi

mkdir -p "${OUT_DIR}"
cp "${CMD_FILE}" "${OUT_DIR}/rastan_fu1_playtrace_debug.cmd"

SUMMARY_PATH="${OUT_DIR}/fu1_summary.txt"
AVI_PATH="${OUT_DIR}/rastan_fu1_playtrace.avi"
STDOUT_PATH="${OUT_DIR}/mame_stdout.log"
STDERR_PATH="${OUT_DIR}/mame_stderr.log"
DEBUG_TMP_PATH="${OUT_DIR}/debug.log"
DEBUG_PATH="${OUT_DIR}/fu1_debugger.log"

echo "FU1 arcade playtrace harness ready."
echo "Insert coin (default key: 5)"
echo "Start game (default key: 1)"
echo "Play at least 2-5 minutes"
echo "Exit MAME normally via File menu or Esc key when done"
echo "Logs and video will be saved to: ${OUT_DIR}"
echo

MAME_ARGS=(
  rastan
  -rompath "${ROM_PATH}"
  -debug
  -debuglog
  -debugscript "${CMD_FILE}"
  -aviwrite "${AVI_PATH}"
  -keepaspect
  -nounevenstretch
  -nofilter
  -prescale 2
  -cheat
  -cheatpath "${REPO_ROOT}/tools/mame/cheat"
)

if [[ -n "${FU1_SECONDS_TO_RUN:-}" ]]; then
  MAME_ARGS+=(-seconds_to_run "${FU1_SECONDS_TO_RUN}")
fi

if [[ -n "${FU1_MAME_EXTRA_ARGS:-}" ]]; then
  # shellcheck disable=SC2206
  EXTRA_ARGS=( ${FU1_MAME_EXTRA_ARGS} )
  MAME_ARGS+=("${EXTRA_ARGS[@]}")
fi

(
  cd "${OUT_DIR}"
  if [[ -n "${FU1_QT_PLATFORM:-}" ]]; then
    export QT_QPA_PLATFORM="${FU1_QT_PLATFORM}"
  fi
  mame "${MAME_ARGS[@]}"
) >"${STDOUT_PATH}" 2>"${STDERR_PATH}" || true

if [[ -f "${DEBUG_TMP_PATH}" ]]; then
  mv -f "${DEBUG_TMP_PATH}" "${DEBUG_PATH}"
elif [[ -f "${REPO_ROOT}/debug.log" ]]; then
  cp -f "${REPO_ROOT}/debug.log" "${DEBUG_PATH}"
fi

{
  echo "FU1 PLAYTRACE SUMMARY"
  echo "Output directory: ${OUT_DIR}"
  echo "Video file: ${AVI_PATH}"
  echo "Debug log: ${DEBUG_PATH}"
  echo "Stdout log: ${STDOUT_PATH}"
  echo "Stderr log: ${STDERR_PATH}"
  echo

  if [[ ! -s "${DEBUG_PATH}" ]]; then
    echo "parsing failed for total writes to 0x00D00000..0x00D007FF (debug log missing or empty)"
    echo "parsing failed for unique writer PCs observed"
    echo "parsing failed for per-writer hit counts"
    echo "parsing failed for descriptor index breakdown"
    echo "parsing failed for writes targeting 0x00D00698"
    echo "parsing failed for breakpoint hit counts"
    echo "parsing failed for unique values written to 0x00D00698"
    exit 0
  fi

  total_wp="$(grep -c '^WP_D00 ' "${DEBUG_PATH}" || true)"
  bp_03ad44="$(grep -c '^BP_03AD44_FILL_PRIMITIVE ' "${DEBUG_PATH}" || true)"
  bp_03c9c2="$(grep -c '^BP_03C9C2_WORD_LOOP ' "${DEBUG_PATH}" || true)"
  bp_510ea="$(grep -c '^BP_510EA_FU1_TARGET ' "${DEBUG_PATH}" || true)"
  bp_510f4="$(grep -c '^BP_510F4_FU1_TARGET ' "${DEBUG_PATH}" || true)"

  echo "Total writes to 0x00D00000..0x00D007FF: ${total_wp}"
  echo

  echo "Per-writer hit counts (arcade_pc):"
  awk '
    /^WP_D00 / {
      pc="";
      for (i=1; i<=NF; i++) {
        if ($i ~ /^pc=/) { pc=substr($i,4); break; }
      }
      if (pc != "") cnt[pc]++;
    }
    END {
      for (pc in cnt) printf "%s %d\n", pc, cnt[pc];
    }
  ' "${DEBUG_PATH}" | sort -k2,2nr -k1,1 || echo "parsing failed for per-writer hit counts"
  echo

  echo "Writes by target descriptor index (addr offset / 8):"
  awk '
    function h2d(h,    i,c,v,n) {
      n=0;
      for (i=1; i<=length(h); i++) {
        c=substr(h,i,1);
        if (c>="0" && c<="9") v=c+0;
        else if (c>="A" && c<="F") v=10 + index("ABCDEF", c) - 1;
        else if (c>="a" && c<="f") v=10 + index("abcdef", c) - 1;
        else v=0;
        n=(n*16)+v;
      }
      return n;
    }
    /^WP_D00 / {
      addr="";
      for (i=1; i<=NF; i++) {
        if ($i ~ /^addr=/) { addr=substr($i,6); break; }
      }
      if (addr != "") {
        ai=h2d(addr);
        di=int((ai - 13631488)/8);
        cnt[di]++;
      }
    }
    END {
      for (di in cnt) printf "%d %d\n", di, cnt[di];
    }
  ' "${DEBUG_PATH}" | sort -n -k1,1 || echo "parsing failed for descriptor index breakdown"
  echo

  d00698_writes="$(awk '/^WP_D00 / { for (i=1; i<=NF; i++) if ($i ~ /^addr=/ && toupper(substr($i,6)) == "D00698") c++ } END { print c+0 }' "${DEBUG_PATH}" || true)"
  echo "Writes targeting 0x00D00698: ${d00698_writes}"
  echo

  echo "Breakpoint hit counts:"
  echo "  0x03AD44: ${bp_03ad44}"
  echo "  0x03C9C2: ${bp_03c9c2}"
  echo "  0x0510EA: ${bp_510ea}"
  echo "  0x0510F4: ${bp_510f4}"
  echo

  echo "Unique values written to 0x00D00698 (post field):"
  awk '
    /^WP_D00 / {
      addr=""; post="";
      for (i=1; i<=NF; i++) {
        if ($i ~ /^addr=/) addr=toupper(substr($i,6));
        else if ($i ~ /^post=/) post=substr($i,6);
      }
      if (addr == "D00698" && post != "") vals[toupper(post)]++;
    }
    END {
      for (v in vals) printf "%s %d\n", v, vals[v];
    }
  ' "${DEBUG_PATH}" | sort -k1,1 || echo "parsing failed for unique values written to 0x00D00698"
} > "${SUMMARY_PATH}"

echo "FU1 playtrace complete."
echo "Summary: ${SUMMARY_PATH}"
echo "Output directory: ${OUT_DIR}"
