#!/usr/bin/env bash
# Builds the Talha Mono families (normal, Wide, Text and their NF) from upstream Radon.
#
# Usage: ./build.sh [python]                    everything
#      FAMILIES="normal wide" STYLES="Regular Italic" ./build.sh python
#                                               just a part (how CI splits the work)
# FAMILIES: normal wide text    STYLES: Regular Bold Italic BoldItalic
# (Text has only Regular and Italic). JOBS: processes at once (default 4).
# HINT_JOBS: workers per autohinter (default 2; use 1 in restricted sandboxes).
# TALHA_BUILD_DIR: isolated output (default build).
set -euo pipefail
cd "$(dirname "$0")"
PY="${1:-python3}"
JOBS="${JOBS:-4}"
HINT_JOBS="${HINT_JOBS:-2}"
FAMILIES="${FAMILIES:-normal wide text}"
STYLES="${STYLES:-Regular Bold Italic BoldItalic}"
NF_DIR="${NF_DIR:-/usr/share/fonts/OTF}"
TALHA_BUILD_DIR="${TALHA_BUILD_DIR:-build}"
mkdir -p "$TALHA_BUILD_DIR"

# Every task runs in the background and each one's exit status is checked:
# a failing merge.py fails the build (a bare `wait` always returns 0, which
# once hid failures). The JOBS limit waits without reaping processes, so no
# status is lost. With everything in parallel the local machine ran out of
# memory.
pids=()
throttle() { while (( $(jobs -rp | wc -l) >= JOBS )); do sleep 0.2; done; }
run() { throttle; "$@" & pids+=("$!"); }
collect() {
  local failed=0
  for p in "${pids[@]}"; do wait "$p" || failed=1; done
  pids=()
  (( failed == 0 )) || { echo "build: a task failed (see the output above)" >&2; exit 1; }
}

style_name() { case "$1" in BoldItalic) echo "Bold Italic" ;; *) echo "$1" ;; esac; }
built=()
for fam in $FAMILIES; do
  case "$fam" in
    normal) prefix=TalhaMono;     flag=() ;;
    wide)   prefix=TalhaMonoWide; flag=(--wide) ;;   # cell 1320, the accessibility build
    text)   prefix=TalhaMonoText; flag=(--text) ;;   # nib 8% wider: light grounds, 97 PPI
    *) echo "unknown family: $fam (expected normal, wide or text)" >&2; exit 2 ;;
  esac
  for file in $STYLES; do
    [[ $fam == text && $file != Regular && $file != Italic ]] && continue
    run "$PY" tools/merge.py "sources/upstream/MonaspaceRadon-$file.otf" "$TALHA_BUILD_DIR/$prefix-$file.otf" \
        --style "$(style_name "$file")" "${flag[@]}"
    built+=("$TALHA_BUILD_DIR/$prefix-$file.otf")
  done
done
collect

# Hinting (roadmap F2): Adobe's autohinter over the pen outlines, so FreeType's
# hintslight can snap baseline, x-height and stems to the pixel grid. Before
# the NF step, so the letters arrive hinted; the icons stay as Nerd Fonts made them.
AUTOHINT="$(dirname "$PY")/otfautohint"
command -v "$AUTOHINT" >/dev/null || AUTOHINT=otfautohint
if command -v "$AUTOHINT" >/dev/null; then
  for f in "${built[@]}"; do
    # i l j q 1 (and t f in the italics) stay unhinted (see tools/nohint.py).
    # Bound the workers: otfautohint opens one process per core; with several files at
    # once that reached 30 processes and ran out of memory.
    run "$AUTOHINT" -p "$HINT_JOBS" -x "$("$PY" tools/nohint.py "$f")" "$f"
  done
  collect
else
  echo "otfautohint not found (pip install afdko): building unhinted fonts" >&2
fi

# NF variant: the Nerd Fonts icons (bar, starship, nvim) inside the font.
# They come from MonaspiceRn Nerd Font of the same style, scaled to this cell.
for f in "${built[@]}"; do
  file="${f##*-}"; file="${file%.otf}"
  src="$NF_DIR/MonaspiceRnNerdFontMono-$file.otf"
  [[ -f $src ]] || { echo "no $src: skipping the NF build of $f" >&2; continue; }
  base="$(basename "$f" .otf)"
  run "$PY" tools/nerd.py "$f" "$src" "$TALHA_BUILD_DIR/${base%-*}NF-$file.otf"
done
collect
ls -la "$TALHA_BUILD_DIR"/TalhaMono*.otf
